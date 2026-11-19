"""Relais réseau de la cage (bibliothèque standard seulement).

La cage n'a pas de réseau (espace de noms réseau vide). Trois services y entrent par des sockets
Unix montées dans la cage :

    exterieur SOCKET HOTE:PORT              hors cage : socket Unix -> service TCP local
    filtre SOCKET JOURNAL DOMAINE[,...]     hors cage : mandataire HTTP CONNECT, domaines autorisés seulement
    interieur PORT SOCKET                   dans la cage : 127.0.0.1:PORT -> socket Unix

Le filtre journalise chaque demande (heure, domaine, port, accepté ou refusé).
"""
import asyncio
import datetime
import json
import sys


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


def filtre(socket, journal, domaines):
    autorises = {d.strip().lower() for d in domaines.split(",") if d.strip()}

    def noter(hote, port, accepte, requete):
        with open(journal, "a") as f:
            f.write(json.dumps({"heure": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                "hote": hote, "port": port, "accepte": accepte,
                                "requete": requete[:200]}, ensure_ascii=False) + "\n")

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
        accepte = hote in autorises and port == "443"
        if not ligne:   # sonde de disponibilité du port (interieur.sh), rien à journaliser
            e.close()
            return
        noter(hote, port, accepte, ligne)
        try:
            if not accepte:
                return await repondre(e, b"403 Forbidden")
            try:
                l2, e2 = await asyncio.open_connection(hote, int(port))
            except OSError:
                return await repondre(e, b"502 Bad Gateway")
            e.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await e.drain()
        except ConnectionError:
            return
        await relier(l, e, l2, e2)

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
