# corsi.py

# Database statico dei corsi ITS ICT Piemonte.
# Usiamo un dizionario Python per mappare ogni corso alle sue materie e competenze.
# Questo dizionario verrà iniettato nei prompt dell'LLM (Context Stuffing).

class CorsoNonValidoError(ValueError):
    """Il corso richiesto non esiste nel catalogo."""
    pass


CORSI_ITS = {
    # --- Area Programmazione e Sviluppo ---
    "Data Manager": {
        "area": "Programmazione e sviluppo",
        "materie": ["Database SQL e NoSQL", "Python per la Data Analysis", "Data Governance", "Cloud Storage", "ETL Processes"],
        "focus_hr": "capacità di organizzare informazioni, precisione, problem solving"
    },
    "Full Stack Developer": {
        "area": "Programmazione e sviluppo",
        "materie": ["HTML/CSS", "JavaScript", "React", "Node.js", "Java o C#", "Database relazionali", "Git"],
        "focus_hr": "lavoro in team, gestione del tempo, adattabilità a nuove tecnologie"
    },
    "Web Solution Architect": {
        "area": "Programmazione e sviluppo",
        "materie": ["Architetture Cloud", "Microservizi", "DevOps", "Sicurezza Web", "Design Pattern", "API REST"],
        "focus_hr": "pensiero critico, capacità di spiegare concetti complessi, leadership"
    },
    "Web e Mobile Developer": {
        "area": "Programmazione e sviluppo",
        "materie": ["Sviluppo Frontend", "Sviluppo Mobile (iOS/Android)", "UI/UX Design", "React Native o Flutter", "Version Control (Git)"],
        "focus_hr": "attenzione all'utente, creatività, capacità di risolvere bug sotto pressione"
    },
    "Software Developer": {
        "area": "Programmazione e sviluppo",
        "materie": ["Algoritmi e Strutture Dati", "Programmazione a Oggetti (OOP)", "C++ o Java", "Testing e Debugging", "Ingegneria del Software"],
        "focus_hr": "metodo, resilienza, gestione dello stress, lavoro di squadra"
    },

    # --- Area Cyber e Cloud ---
    "AWS Cloud Architect": {
        "area": "Cyber e Cloud",
        "materie": ["Amazon Web Services (AWS)", "Infrastruttura come Codice (IaC)", "Networking Cloud", "Sicurezza Cloud", "Terraform"],
        "focus_hr": "visione strategica, gestione del rischio, problem solving"
    },
    "Cloud Specialist": {
        "area": "Cyber e Cloud",
        "materie": ["Fondamenti di Cloud Computing", "Docker e Kubernetes", "Virtualizzazione", "Microsoft Azure o Google Cloud", "Linux Server"],
        "focus_hr": "adattabilità, gestione delle crisi, precisione"
    },
    "SOC Analyst": {
        "area": "Cyber e Cloud",
        "materie": ["Security Information and Event Management (SIEM)", "Analisi dei Log", "Incident Response", "Threat Intelligence", "Firewall e IDS/IPS"],
        "focus_hr": "attenzione estrema ai dettagli, gestione dello stress in situazioni di emergenza, pensiero analitico"
    },
    "Cyber Threat Analyst": {
        "area": "Cyber e Cloud",
        "materie": ["Malware Analysis", "Penetration Testing", "Reverse Engineering", "OSINT", "Cyber Threat Intelligence"],
        "focus_hr": "curiosità, pensiero fuori dagli schemi, etica, resilienza"
    },
    "Cyber Security Specialist": {
        "area": "Cyber e Cloud",
        "materie": ["Crittografia", "Sicurezza delle Reti", "Sicurezza delle Applicazioni", "Gestione delle Identità", "Compliance e GDPR"],
        "focus_hr": "comunicazione chiara (anche a non tecnici), affidabilità, etica professionale"
    },

    # --- Area AI & Data ---
    "GenAI Specialist": {
        "area": "AI & Data",
        "materie": ["Large Language Models (LLM)", "Prompt Engineering", "Python per l'AI", "API OpenAI/Gemini", "Vector Database (es. ChromaDB)"],
        "focus_hr": "creatività, capacità di sperimentare, adattabilità a un settore in rapidissimo cambiamento"
    },
    "Data Analyst and AI Specialist": {
        "area": "AI & Data",
        "materie": ["Python (Pandas, NumPy)", "Machine Learning", "Statistica", "Data Visualization (PowerBI/Tableau)", "SQL"],
        "focus_hr": "capacità di raccontare storie con i dati, precisione, pensiero critico"
    },

    # --- Area Comunicazione e Entertainment ---
    "Digital Twin and 3D Specialist": {
        "area": "Comunicazione e Entertainment",
        "materie": ["Modellazione 3D (Blender/Maya)", "Realtà Aumentata (AR)", "Realtà Virtuale (VR)", "Unity o Unreal Engine", "Animazione"],
        "focus_hr": "creatività, lavoro di squadra (tra artisti e programmatori), gestione delle scadenze creative"
    },
    "Digital Strategist": {
        "area": "Comunicazione e Entertainment",
        "materie": ["Digital Marketing", "Social Media Management", "SEO/SEM", "Data Analytics", "Content Creation"],
        "focus_hr": "comunicazione persuasiva, leadership, orientamento ai risultati"
    }
}

# Funzione di utilità per recuperare in modo sicuro i dati di un corso
def get_dettagli_corso(nome_corso: str) -> dict:
    """
    Recupera i dettagli di un corso. 
    Dato che il frontend usa un menu fisso, ci aspettiamo che il corso esista.
    Se per qualche motivo (bug o chiamata API diretta) il corso non esiste, 
    solleviamo un errore esplicito per evitare che l'LLM generi domande a caso.
    """
    if nome_corso not in CORSI_ITS:
        raise CorsoNonValidoError(
            f"Corso non valido: '{nome_corso}'. Selezionare un corso dal menu."
        )
    
    return CORSI_ITS[nome_corso]