# Domanda 2 — "Cosa ti spaventa di più all'idea di fare un colloquio?"
PAURE_DISPONIBILI = [
    "Restare senza parole",
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso",
]

# Domanda 3 — "Quando ti trovi di fronte a un problema difficile, come reagisci?"
STILI_GESTIONE_PROBLEMI = [
    "Mi blocco e mi faccio prendere dal panico",
    "Chiedo subito aiuto a un collega o a un tutor",
    "Faccio ricerche infinite finché non trovo la soluzione",
    "Mi prendo una pausa e ci riprovo con calma",
]

# Domanda 4 — "Se il colloquio andasse male, quale pensi sarebbe il motivo principale?"
TIMORI_CRITICI = [
    "Non ho saputo spiegare bene le mie competenze",
    "Ero troppo in ansia e non riuscivo a concentrarmi",
    "Non ho abbastanza esperienza tecnica per il ruolo",
    "Non mi sono preparato abbastanza sull'azienda",
]

# Metrica che misura la paura della Domanda 2.
# La paura è superata quando QUESTA metrica arriva a 7.5/10.
METRICA_PER_PAURA = {
    "Restare senza parole": "chiarezza",
    "Non sembrare abbastanza preparato tecnicamente": "esempi_concreti",
    "Fare una figuraccia con il recruiter": "struttura_star",
    "Non saper parlare di me stesso": "chiarezza",
}

SOGLIA_METRICA_PAURA = 7.5
