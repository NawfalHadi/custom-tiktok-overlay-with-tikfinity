# How?!
run the tikfinity first while live on titok.
or you can just start the main.py

> ./main.py

# Tunnel
because titok live studio didnt allow you to use
local ip like 127.0.0.1. we need create
something to make sure it shows on tiktok live studio

### using cloudflared.exe
put on the same path to give easier to find
then run this with the same local ip in powershell

> .\cloudflared.exe tunnel --url http://localhost:5000