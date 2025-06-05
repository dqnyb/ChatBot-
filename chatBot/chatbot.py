from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
from openpyxl import Workbook, load_workbook
from datetime import datetime

import pandas as pd
import os
import random

app = Flask(__name__)
CORS(app)

# Pentru acest proiect am lăsat cheia publică (pentru a fi testată mai repede), dar desigur că nu se face așa!
# Aș fi folosit client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) și aș fi dat export în env la key: export OPENAI_API_KEY="sk-..."

client = OpenAI(
    api_key="",  # pune aici cheia ta reală!
)


def log_message(sender, message):
    # Creează calea absolută către folderul logs ! Pentru a salva log-urile in excel !
    base_dir = os.path.expanduser("../logs")
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, "chat_log1.xlsx")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {"Timestamp": timestamp, "Sender": sender, "Message": message}

    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_excel(file_path, index=False)
        print(f"[{timestamp}] [LOGGED] {sender}: {message}")
    except Exception as e:
        print(f"[EROARE] Logarea a eșuat: {e}")


@app.route("/start", methods=["GET"])
def start():
    contexts = [
        "într-o conversație relaxată",
        "la începutul unei discuții casual",
        "când întâlnești pe cineva nou",
        "într-un chat prietenos",
        "într-un context informal"
    ]
    hint = random.choice(contexts)

    name_prompt = (
        f"Generează o întrebare scurtă și prietenoasă prin care să ceri utilizatorului să-și spună numele (fă să pari entuziasmat). Mereu înainte de a întreba, dă salut. "
        f"Formularea trebuie să fie naturală, clară și fără exagerări. "
        f"Imaginează-ți că ești {hint}."
    )

    ask_name = ask_with_ai(name_prompt)
    log_message("AI BOT", ask_name)

    return jsonify({"ask_name": ask_name})


@app.route("/interests", methods=["POST"])
def interests():
    user_data = request.get_json()
    name = user_data.get("name", "prieten")

    log_message("USER", name)

    interests_prompt = (
        f"Adresează-te utilizatorului pentru a-l întreba ce interese sau hobby-uri are. "
        f"Dacă valoarea '{name}' pare un nume propriu (ex: Andrei, Maria etc.), folosește acel nume în mesaj. "
        f"Generează o întrebare naturală și prietenoasă prin care să afli ce interese sau hobby-uri are utilizatorul. "
        f"Adresează-te direct utilizatorului. Fii creativ și nu repeta aceeași formulare."
    )

    ask_interests = ask_with_ai(interests_prompt)
    log_message("AI BOT", ask_interests)

    return jsonify({"ask_interests": ask_interests})


@app.route("/welcome", methods=["POST"])
def welcome():
    data = request.json
    name = data.get("name", "")
    interests = data.get("interests", "")

    log_message("USER", interests)

    welcome_msg = generate_welcome_message(name, interests)
    log_message("AI BOT", welcome_msg)

    return jsonify({"message": welcome_msg})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")

    log_message("USER", message)

    messages = build_messages(name, interests)
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        reply = response.choices[0].message.content.strip()
        log_message("AI BOT", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_welcome_message(name, interests):
    system_prompt = (
        f"Ești un chatbot inteligent, prietenos și util. Evită să repeți saluturi precum „Salut”, „Bine ai venit” sau numele utilizatorului ({name}) în fiecare mesaj. "
        f"Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
        f"Generează un mesaj foarte scurt și natural, mai scurt de 80 de tokenuri, "
        f"referitor la interesele mele: {interests}. "
        f"Mesajul trebuie să fie cald și încurajator, fără introduceri formale. "
        f"Mesajul trebuie să se termine exact cu: „Cu ce te pot ajuta astăzi?” "
        f"Nu adăuga alte întrebări sau fraze suplimentare. "
        f"Nu saluta, nu repeta numele, doar treci direct la subiect. "
        f"Mereu când ești întrebat de vreo preferință, sfat, alegere sau orice, fă referire la {interests} mele și apoi spune și ceva adițional."
    )
    messages = [{"role": "system", "content": system_prompt}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.9,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()


def ask_with_ai(prompt_instruction):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt_instruction}
        ],
        temperature=0.9,
        max_tokens=80
    )
    return response.choices[0].message.content.strip()


def get_user_info():
    name_prompt = (
        "Generează o întrebare scurtă și prietenoasă prin care să ceri utilizatorului să-și spună numele. "
        "Întrebarea trebuie să înceapă cu un salut simplu, cum ar fi „Salut”, „Bună” sau „Hei”. "
        "Formularea trebuie să fie naturală, clară și fără exagerări. "
        "Evită expresii siropoase sau prea entuziaste (ex: „Ce nume frumos”, „dezvăluie”). "
        "Păstrează un ton prietenos, dar echilibrat. Variază formulările între rulări."
    )
    interests_prompt = (
        "Generează o întrebare naturală și prietenoasă prin care să afli ce interese sau hobby-uri are utilizatorul. "
        "Fii creativ și nu repeta aceeași formulare."
    )

    ask_name = ask_with_ai(name_prompt)
    name = input(ask_name + " ")

    ask_interests = ask_with_ai(interests_prompt)
    interests = input(f"{ask_interests} ")

    return name, interests


def build_messages(name, interests):
    system_prompt = (
        f"Răspunsul să fie mai scurt de 250 de tokenuri. "
        f"Utilizatorul se numește {name} și este interesat de: {interests}. "
        f"Ajută-l să își atingă obiectivele prin răspunsuri precise și relevante. "
        f"Fă referire la {interests} de fiecare dată când îi propui ceva, ține cont de ceea ce îi place. Pe lângă asta, poți adăuga și alte variante. "
        f"Dacă utilizatorul are intenția de a încheia discuția, dacă formulează fraze de adio, atunci încheie discuția elegant. "
        f"Ești un chatbot inteligent, prietenos și util. Evită să repeți saluturi precum „Salut”, „Bine ai venit” sau numele utilizatorului ({name}) în fiecare mesaj. "
        f"Răspunde direct, personalizat, scurt și clar, ca și cum conversația este deja în desfășurare. "
        f"Dacă utilizatorul îți zice că nu mai vrea să audă așa mult despre {interests}, atunci schimbă puțin subiectul. "
        f"Ești un chatbot inteligent, prietenos și util. Pe utilizator îl cheamă {name}, "
        f"și este interesat de: {interests}. Oferă răspunsuri personalizate, scurte și clare. Arată cât mai evident că știi acea persoană și ajut-o să își atingă obiectivele prin răspunsuri clare și bine puse la punct!"
    )
    return [{"role": "system", "content": system_prompt}]


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
