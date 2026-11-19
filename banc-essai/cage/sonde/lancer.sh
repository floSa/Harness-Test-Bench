#!/bin/bash
# « Harnais » de preuve du lot 3 : lance la sonde de la cage (argument : chemin hôte du test caché).
exec python3 /opt/harnais/sonde.py "$@"
