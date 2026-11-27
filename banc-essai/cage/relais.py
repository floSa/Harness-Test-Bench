"""Relais réseau de la cage (bibliothèque standard seulement).

La cage n'a pas de réseau (espace de noms réseau vide). Trois services y entrent par des sockets
Unix montées dans la cage :

    exterieur SOCKET HOTE:PORT              hors cage : socket Unix -> service TCP local
    filtre SOCKET JOURNAL DOMAINE[,...] [QUOTA]
                                            hors cage : mandataire HTTP CONNECT, domaines autorisés
                                            seulement (« .hf.co » : sous-domaines), volume plafonné
    interieur PORT SOCKET                   dans la cage : 127.0.0.1:PORT -> socket Unix

Le filtre journalise chaque demande (heure, domaine, port, accepté ou refusé) et chaque tunnel
fermé (octets reçus et envoyés).
"""
import asyncio
import base64
import datetime
import json
import os
import sys
import urllib.parse


async def pomper(lecteur, ecrivain):
    try:
        while data := await lecteur.read(65536):
            ecrivain.write(data)
            await ecrivain.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        try:
            ecrivain.close()
        except Exception:
            pass


async def relier(l1, e1, l2, e2):
    await asyncio.gather(pomper(l1, e2), pomper(l2, e1))


def exterieur(socket, cible):
    hote, port = cible.rsplit(":", 1)

    async def client(l, e):
        try:
            l2, e2 = await asyncio.open_connection(hote, int(port))
        except OSError:
            e.close()
            return
        await relier(l, e, l2, e2)

    async def main():
        s = await asyncio.start_unix_server(client, path=socket)
        async with s:
            await s.serve_forever()
    asyncio.run(main())


def interieur(port, socket):
    async def client(l, e):
        try:
            l2, e2 = await asyncio.open_unix_connection(socket)
        except OSError:
            e.close()
            return
        await relier(l, e, l2, e2)

    async def main():
        s = await asyncio.start_server(client, "127.0.0.1", int(port))
        async with s:
            await s.serve_forever()
    asyncio.run(main())


def autorise(hote, motifs):
    """Domaine exact, ou sous-domaine d'un motif commençant par un point (« .hf.co »)."""
    if not hote:
        return False
    return any(hote == m or (m.startswith(".") and (hote.endswith(m) or hote == m[1:])) for m in motifs)


def filtre(socket, journal, domaines, quota="0"):
    """Mandataire CONNECT : domaines autorisés, port 443, volume total plafonné (quota en octets,
    0 = sans plafond), par le mandataire de l'entreprise si BANC_MANDATAIRE est défini. Chaque demande est journalisée ; chaque tunnel aussi à sa fermeture, avec les
    octets reçus et envoyés. Quota atteint : tunnels ouverts coupés, nouvelles demandes refusées."""
    motifs = {d.strip().lower() for d in domaines.split(",") if d.strip()}
    # Poste d'entreprise : tunnels ouverts par le mandataire sortant (http://[id:mdp@]hote:port).
    amont = urllib.parse.urlsplit(os.environ["BANC_MANDATAIRE"]) if os.environ.get("BANC_MANDATAIRE") else None
    plafond = int(quota)
    total = {"octets": 0, "depasse": False}
    tunnels = set()

    def noter(**champs):
        with open(journal, "a") as f:
            f.write(json.dumps({"heure": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
                               | champs, ensure_ascii=False) + "\n")

    async def compter(lecteur, ecrivain, compte, cle):
        try:
            while data := await lecteur.read(65536):
                compte[cle] += len(data)
                total["octets"] += len(data)
                if plafond and total["octets"] > plafond:
                    if not total["depasse"]:
                        total["depasse"] = True
                        noter(evenement="quota_atteint", octets_total=total["octets"], quota=plafond)
                        for t in list(tunnels):
                            t.close()
                    break
                ecrivain.write(data)
                await ecrivain.drain()
        except (ConnectionError, asyncio.IncompleteReadError, OSError):
            pass
        finally:
            try:
                ecrivain.close()
            except Exception:
                pass

    async def client(l, e):
        try:
            ligne = (await asyncio.wait_for(l.readline(), 30)).decode("latin-1").strip()
            while (await asyncio.wait_for(l.readline(), 30)) not in (b"\r\n", b"\n", b""):
                pass
        except (asyncio.TimeoutError, ConnectionError, ValueError, asyncio.LimitOverrunError):
            # délai, connexion coupée ou ligne d'en-tête trop longue : refus sans réponse
            e.close()
            return
        parties = ligne.split()
        hote, port = None, None
        if len(parties) >= 2 and parties[0].upper() == "CONNECT" and ":" in parties[1]:
            hote, port = parties[1].rsplit(":", 1)
            hote = hote.strip("[]").lower()
        if not ligne:   # sonde de disponibilité du port (interieur.sh), rien à journaliser
            e.close()
            return
        accepte = autorise(hote, motifs) and port == "443" and not total["depasse"]
        noter(evenement="demande", hote=hote, port=port, accepte=accepte, requete=ligne[:200],
              quota_atteint=total["depasse"])
        try:
            if not accepte:
                return await repondre(e, b"403 Forbidden")
            try:
                l2, e2 = await ouvrir(hote, int(port))
            except (OSError, ConnectionError, asyncio.TimeoutError):
                return await repondre(e, b"502 Bad Gateway")
            e.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await e.drain()
        except ConnectionError:
            return
        compte = {"recus": 0, "envoyes": 0}
        tunnels.update((e, e2))
        try:
            await asyncio.gather(compter(l2, e, compte, "recus"), compter(l, e2, compte, "envoyes"))
        finally:
            tunnels.discard(e)
            tunnels.discard(e2)
            noter(evenement="fin", hote=hote, octets_recus=compte["recus"], octets_envoyes=compte["envoyes"])

    async def ouvrir(hote, port):
        """Connexion directe, ou tunnel par le mandataire de l'entreprise (BANC_MANDATAIRE)."""
        if not amont:
            return await asyncio.open_connection(hote, port)
        l2, e2 = await asyncio.open_connection(amont.hostname, amont.port or 8080)
        auth = b""
        if amont.username:
            jeton = base64.b64encode(f"{urllib.parse.unquote(amont.username)}:"
                                     f"{urllib.parse.unquote(amont.password or '')}".encode())
            auth = b"Proxy-Authorization: Basic " + jeton + b"\r\n"
        e2.write(f"CONNECT {hote}:{port} HTTP/1.1\r\nHost: {hote}:{port}\r\n".encode() + auth + b"\r\n")
        await e2.drain()
        statut = await asyncio.wait_for(l2.readline(), 30)
        while (await asyncio.wait_for(l2.readline(), 30)) not in (b"\r\n", b"\n", b""):
            pass
        if b" 200" not in statut:
            e2.close()
            raise ConnectionError(f"mandataire de l'entreprise : {statut[:80]!r}")
        return l2, e2

    async def repondre(e, statut):
        e.write(b"HTTP/1.1 " + statut + b"\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        await e.drain()
        e.close()

    async def main():
        s = await asyncio.start_unix_server(client, path=socket)
        async with s:
            await s.serve_forever()
    asyncio.run(main())


if __name__ == "__main__":
    mode, *args = sys.argv[1:]
    try:
        {"exterieur": exterieur, "interieur": interieur, "filtre": filtre}[mode](*args)
    except KeyboardInterrupt:
        pass
