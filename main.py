import os
import json
import asyncio
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
CG_API_KEY = os.getenv("COINGECKO_API_KEY")

if not api_key:
    raise RuntimeError("HATA: OPENAI_API_KEY bulunamadı!")

if not CG_API_KEY:
    raise RuntimeError("HATA: COINGECKO_API_KEY bulunamadı!")



client = AsyncOpenAI(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageDict(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[MessageDict] = []

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

if CG_API_KEY:
    HEADERS["x-cg-demo-api-key"] = CG_API_KEY

# --- COINGECKO Functions ---
async def get_crypto_price(coin_id: str):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    print(f"\n{'='*50}\n🔍 DEBUG [FİYAT]: {coin_id} için CoinGecko'ya gidiliyor...\nURL: {url}")

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=HEADERS, timeout=10.0)

            print(f"📡 HTTP STATUS: {response.status_code}")
            print(f"📦 RAW RESPONSE: {response.text}")

            if response.status_code == 200:
                data = response.json()
                price = data.get(coin_id, {}).get("usd")
                print(f"✅ BAŞARILI: {coin_id} Fiyatı = {price}$")
                return price
            else:
                print(f"🚨 HATA: CoinGecko {response.status_code} döndürdü. Yedek fiyata geçiliyor.")
                return 0

    except Exception as e:
        print(f"💥 KRİTİK HATA (Fiyat): İstek atılamadı! Detay: {e}")
        return 0
    finally:
        print('='*50 + '\n')

async def get_crypto_history(coin_id: str, days: int = 7):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    print(f"\n{'='*50}\n📈 DEBUG [GRAFİK]: {coin_id} geçmiş verisi çekiliyor...\nURL: {url}")

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=HEADERS, timeout=10.0)

            print(f"📡 HTTP STATUS: {response.status_code}")

            if response.status_code == 200:
                prices = [item[1] for item in response.json().get("prices", [])]
                print(f"✅ BAŞARILI: {len(prices)} adet veri noktası çekildi.")
                return prices
            else:
                print(f"🚨 HATA: Grafik API {response.status_code} döndürdü. Detay: {response.text[:100]}...")
                return None

    except Exception as e:
        print(f"💥 KRİTİK HATA (Grafik): İstek atılamadı! Detay: {e}")
        return None
    finally:
        print('='*50 + '\n')

# --- OPENAI TOOL
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_data",
            "description": "SADECE tek bir kripto paranın piyasa trendini veya ÇİZGİ GRAFİĞİNİ görmek istediğinde kullan. EĞER KULLANICI KENDİ PORTFÖYÜNDEN, CÜZDANINDAN VEYA ELİNDEKİ MİKTARLARDAN (örn: 0.5 BTC) BAHSEDİYORSA BU ARACI ASLA KULLANMA!",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "CoinGecko ID'si (Örn: bitcoin, ethereum, solana)"
                    },

                    "days": {
                        "type": "integer",
                        "description": "Kullanıcının istediği geçmiş veri gün sayısı. Örn: '1 ay' derse 30, '2 hafta' derse 14, '1 yıl' derse 365, '5 gün' derse 5 gönder. Eğer kullanıcı süre belirtmezse varsayılan olarak 7 gönder."
                    }
                },
                "required": ["coin_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_portfolio",
            "description": "Kullanıcı kendi portföyünden veya elindeki coin miktarlarından bahsettiğinde SADECE BU ARACI KULLAN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "description": "Kullanıcının elindeki kripto paraların listesi.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "coin_id": {
                                    "type": "string",
                                    "description": "Coin'in İngilizce tam adı (örn: bitcoin, ethereum, solana)"
                                },
                                "amount": {
                                    "type": "number",
                                    "description": "Kullanıcının sahip olduğu miktar (örn: 0.25, 4)"
                                }
                            },
                            "required": ["coin_id", "amount"]
                        }
                    }
                },
                "required": ["assets"]
            }
        }
    }
]


COIN_COLORS = {"bitcoin": "#F7931A", "ethereum": "#627EEA", "solana": "#14F195", "tether": "#26A17B"}

async def get_portfolio_distribution(assets: list):
    items = []
    total_value = 0

    for asset in assets:
        coin_id = asset.get("coin_id", "").lower()
        amount = asset.get("amount", 0)

        price = await get_crypto_price(coin_id)
        if price is None:
            price = 0

        value = float(amount) * price
        total_value += value

        items.append({
            "name": coin_id.capitalize(),
            "value": round(value, 2),
            "color": COIN_COLORS.get(coin_id, "#8884d8")
        })

    return items, total_value

@app.post("/chat")
async def chat_with_ai(request: ChatRequest):


    messages = [{"role": "system", "content": """Sen FinChat adında profesyonel, bilgili ve konuşkan bir yapay zeka finans asistanısın. 
    ÇOK ÖNEMLİ KURALLAR:
    1. Kullanıcı kendi coin miktarlarından (örn: '0.25 BTC') bahsederse, ASLA kendi içinde matematiksel hesaplama yapma! SADECE `calculate_portfolio` aracını çağır.
    2. Kullanıcı FİYAT veya GRAFİK sorarsa KESİNLİKLE `get_crypto_data` aracını kullan.
    3. Aracı kullandıktan sonra kısa cevaplar verme! Kullanıcıya gelen veri üzerinden detaylı, profesyonel ve bilgilendirici bir finansal yorum yap. Fiyatı söyle, trendi yorumla.
    4. KESİNLİKLE Markdown resim ekleme kodu (örneğin: ![grafik](url) veya metin karakterleriyle çizim) KULLANMA! Senin yerine grafiği zaten arayüz çizecektir. Sen sadece zengin metin analizine odaklan."""}]

    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": request.message})

    async def response_generator():
        try:
            # ADIM 1: OpenAI'a soruyoruz "Araç kullanman lazım mı?"
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            ai_message = response.choices[0].message


            if ai_message.tool_calls:
                messages.append(ai_message.model_dump(exclude_none=True))

                chart_data_to_send = None
                portfolio_data_to_send = None

                for tool_call in ai_message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    # 1. TOOL: Price and Graph
                    if function_name == "get_crypto_data":
                        coin_id = arguments.get("coin_id", "bitcoin")

                        days = arguments.get("days", 7)

                        price = await get_crypto_price(coin_id)
                        chart_data = await get_crypto_history(coin_id, days)

                        interval_label = "Saat" if days <= 90 else "Gün"
                        chart_title = f"{days} Günlük Fiyat Trendi ({'Saatlik' if days <= 90 else 'Günlük'} Veri)"

                        chart_data_to_send = {
                            "prices": chart_data,
                            "title": chart_title,
                            "interval": interval_label
                        }

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps({"price": price, "chart_data": chart_data})
                        })

                    # 2. TOOL: Portfolio
                    elif function_name == "calculate_portfolio":

                        print("\n" + "="*50)
                        print("🚀 DEBUG: PORTFÖY ARACI BAŞARIYLA TETİKLENDİ!")
                        print("Gelen Veri:", arguments)
                        print("="*50 + "\n")

                        assets = arguments.get("assets", [])
                        portfolio_items, total_value = await get_portfolio_distribution(assets)
                        portfolio_data_to_send = portfolio_items

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps({
                                "portfolio_distribution": portfolio_items,
                                "total_usd_value": total_value
                            })
                        })


                stream = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    stream=True
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content


                if chart_data_to_send or portfolio_data_to_send:
                    metadata = {}
                    if chart_data_to_send:
                        metadata["chartData"] = chart_data_to_send
                    if portfolio_data_to_send:
                        metadata["portfolioData"] = portfolio_data_to_send

                    yield f"\n[METADATA]{json.dumps(metadata)}"

            else:
                stream = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

        except openai.RateLimitError:
            yield "SİSTEM UYARISI: OpenAI API bakiyeniz yetersiz veya limitinize ulaştınız. Lütfen platform.openai.com üzerinden bakiye yükleyin."
        except openai.AuthenticationError:
            yield "SİSTEM UYARISI: OpenAI API Anahtarı geçersiz. Lütfen .env dosyanızı kontrol edin."
        except Exception as e:
            yield f"SİSTEM BEKLENMEYEN HATA: {str(e)}"

    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )