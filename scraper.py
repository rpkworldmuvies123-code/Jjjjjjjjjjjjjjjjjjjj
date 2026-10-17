import os
import asyncio
import csv
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# ================= CONFIGURATION =================
API_ID = 34964566
API_HASH = '0e1adb6860c9e1a4269c87b22ecfd46a'
SESSION_STRING = os.environ.get('TG_SESSION') # Render ke environment se aayega
SOURCE_GROUP = 'https://t.me/NIFTYSENSEX_12' # Jahan se members nikalne hain
# =================================================

# Render free tier ke liye dummy web server
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Scraper is Running...")
        # Trigger scraping in background
        threading.Thread(target=run_scraper, daemon=True).start()

def run_dummy_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

def run_scraper():
    async def main():
        print("1. Script start ho rahi hai...", flush=True)
        if not SESSION_STRING:
            print("ERROR: TG_SESSION nahi mila!", flush=True)
            return
            
        async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
            try:
                print(f"2. Group connect ho raha hai: {SOURCE_GROUP}", flush=True)
                group = await client.get_entity(SOURCE_GROUP)
                print(f"3. Group mil gaya. Members nikalne shuru...", flush=True)
            except Exception as e:
                print(f"ERROR: Group connect nahi hua: {e}", flush=True)
                return

            filename = 'classy_market_members.csv'
            total_count = 0
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['username', 'user_id', 'access_hash'])
                
                offset = 0
                limit = 200
                
                while True:
                    try:
                        participants = await client(GetParticipantsRequest(
                            channel=group, filter=ChannelParticipantsSearch(''),
                            offset=offset, limit=limit, hash=0
                        ))
                    except FloodWaitError as e:
                        print(f"Flood wait: {e.seconds} seconds ka wait karein...", flush=True)
                        await asyncio.sleep(e.seconds + 5)
                        continue
                    except Exception as e:
                        print(f"ERROR fetch karte waqt: {e}", flush=True)
                        break
                    
                    if not participants.users:
                        print("4. Saare members check ho gaye.", flush=True)
                        break
                        
                    for user in participants.users:
                        if user.username: # Sirf unhe save karein jinka username ho
                            writer.writerow([user.username, user.id, user.access_hash])
                            total_count += 1
                    
                    offset += len(participants.users)
                    print(f"Abhi tak {total_count} members mil chuke hain...", flush=True)
                    
                    await asyncio.sleep(2) # Telegram block se bachne ke liye gap
            
            print(f"5. Success! Total {total_count} members ki details save ho gayi.", flush=True)
            
            # File ko Base64 me convert karke Render logs me print karein
            with open(filename, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode('utf-8')
                print("\n\n--- START OF CSV DATA ---", flush=True)
                # Data bahut lamba hota hai, isliye 2000 character ke chunks me print karein
                chunk_size = 2000
                for i in range(0, len(encoded_string), chunk_size):
                    print(encoded_string[i:i+chunk_size], flush=True)
                print("--- END OF CSV DATA ---", flush=True)

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Main thread error: {e}", flush=True)

if __name__ == '__main__':
    run_dummy_server()
