curl -s -m 5 -o /dev/null https://pypi.org && echo "PROBLÈME : Internet accessible" || echo "OK : pas d'Internet"
env | grep -q IAG_CLE && echo "PROBLÈME : clé du portail visible" || echo "OK : clé du portail absente"
echo "Dossiers personnels visibles : $(ls /home)  (attendu : agent)"
echo "Fausse clé : $(curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer faux' $OPENAI_BASE_URL/models)  (attendu : 401)"
curl -s $OPENAI_BASE_URL/chat/completions -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\": \"$MODELE\", \"messages\": [{\"role\": \"user\", \"content\": \"Réponds OK\"}]}"; echo
