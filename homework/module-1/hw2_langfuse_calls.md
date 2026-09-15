
## Part E

Create a session:

```
curl -s -X POST http://localhost:8010/sessions -H 'Content-Type: application/json' -d '{"user_id":1,"role":"shopper"}'
```

Message requests:

```
export SESSION_ID=218530fb2c2141249d872f457f05b187
export TOKEN=eyJpc3N1ZWRfYXQiOiAxNzg5NDI0ODkyLjM5Mzk1MSwgInJvbGUiOiAic2hvcHBlciIsICJzZXNzaW9uX2lkIjogIjIxODUzMGZiMmMyMTQxMjQ5ZDg3MmY0NTdmMDViMTg3IiwgInN0b3JlX2lkIjogbnVsbCwgInVzZXJfaWQiOiAxfQ==.b385760ed43be1511774d0db8ab47c7a8bbce04fb92be0c2f3a1a7a86209b5d1
export MESSAGE1="What is the status of order 4127?"
export MESSAGE2="I would like a refund for order number 3980."
export MESSAGE3="I would like a refund for order 4455."
export MESSAGE4="I want to buy something from Juniper Home Goods. When is the longest refund date?"
export MESSAGE5="Can you give me advice on what car to buy?"
export MESSAGE6="Can you change the email address on my Cartwheel account to new@example.com?"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE1\"}"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE2\"}"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE3\"}"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE4\"}"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE5\"}"
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE6\"}"
```

Trying to get a permissions denial:

```
export MESSAGE7="Can you tell me which users have shopped at home and kitchen stores?"
curl -s -X POST http://localhost:8010/sessions -H 'Content-Type: application/json' -d '{"user_id":9001,"role":"merchant"}'
export SESSION_ID=2d4c57fc3db04fb4a4522959f088ac71
export TOKEN=eyJpc3N1ZWRfYXQiOiAxNzg5NDM2NjIzLjI1MDQ2MDksICJyb2xlIjogIm1lcmNoYW50IiwgInNlc3Npb25faWQiOiAiMmQ0YzU3ZmMzZGIwNGZiNGE0NTIyOTU5ZjA4OGFjNzEiLCAic3RvcmVfaWQiOiAxLCAidXNlcl9pZCI6IDkwMDF9.f4a4e637df6a815d875724793ecf8e8a95ad6b4d74320206d66d287c8a01db4f
curl -s -X POST http://localhost:8010/sessions/$SESSION_ID/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "{\"message\":\"$MESSAGE7\"}"


```
