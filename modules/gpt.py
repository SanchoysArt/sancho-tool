import asyncio
from telethon import events
from g4f.client import Client as G4FClient

def register(client):
    g4f_client = G4FClient()

    @client.on(events.NewMessage(pattern=r'\.gpt (.+)', outgoing=True))
    async def handle_gpt(event):
        """Обработчик команды .gpt"""
        prompt = event.pattern_match.group(1)
        
        try:
            await event.edit("🤖 **GPT думает...**")
            
            # Генерируем ответ через G4F
            response = await asyncio.to_thread(
                lambda: g4f_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500
                )
            )
            
            if not response.choices or not response.choices[0].message.content:
                await event.edit("❌ Пустой ответ от модели")
                return
                
            answer = response.choices[0].message.content.strip()
            
            # Обрезаем если слишком длинное
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
                
            await event.edit(f"🤖 **GPT-4:**\n\n{answer}")
            
        except Exception as e:
            await event.edit(f"❌ Ошибка: {str(e)}")

    print("✅ Модуль GPT загружен!")
