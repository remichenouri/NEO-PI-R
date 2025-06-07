# -*- coding: utf-8 -*-
"""
Application Streamlit pour le Test NEO PI-R
Test de Personnalité des Big Five en ligne gratuit
Inspiré du design de depistage-autisme.streamlit.app
"""

# ================= CONFIGURATION INITIALE =================
# DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
import streamlit as st

st.set_page_config(
    page_title="Test NEO PI-R",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= IMPORTS APRÈS LA CONFIGURATION =================
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import base64
import hashlib
import os
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
import streamlit.components.v1 as components
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime, timedelta
import uuid
import secrets
import time
import scipy.stats as stats
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt

# ================= CLASSES DE GESTION =================

class SecurityManager:
    """Gestionnaire de sécurité pour les données utilisateur"""

    def __init__(self):
        self.key = self._generate_key()
        self.cipher_suite = Fernet(self.key)

    def _generate_key(self):
        """Génère une clé de chiffrement"""
        password = b"NEO_PIR_SECURE_2024"
        salt = b"neo_salt_2024"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt_data(self, data):
        """Chiffre les données"""
        if isinstance(data, dict):
            data = json.dumps(data)
        elif not isinstance(data, str):
            data = str(data)
        return self.cipher_suite.encrypt(data.encode())

    def decrypt_data(self, encrypted_data):
        """Déchiffre les données"""
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            st.error(f"Erreur de déchiffrement : {str(e)}")
            return None

class NEOPIRManager:
    """Gestionnaire principal du test NEO PI-R"""

    def __init__(self):
        self.dimensions = {
            'N': 'Neuroticisme',
            'E': 'Extraversion',
            'O': 'Ouverture',
            'A': 'Agréabilité',
            'C': 'Conscienciosité'
        }

        self.facets = {
            'N': ['Anxiété', 'Hostilité', 'Dépression', 'Timidité sociale', 'Impulsivité', 'Vulnérabilité'],
            'E': ['Chaleur', 'Grégarité', 'Assertivité', 'Activité', 'Recherche de sensations', 'Émotions positives'],
            'O': ['Fantaisie', 'Esthétique', 'Sentiments', 'Actions', 'Idées', 'Valeurs'],
            'A': ['Confiance', 'Droiture', 'Altruisme', 'Compliance', 'Modestie', 'Sensibilité'],
            'C': ['Compétence', 'Ordre', 'Sens du devoir', 'Recherche de réussite', 'Autodiscipline', 'Délibération']
        }

        self.load_questions()

    def load_questions(self):
        """Charge les questions du NEO PI-R (version courte)"""
        self.questions = [
            # Neuroticisme (N1-N12)
            {"id": "N1", "text": "Je me sens souvent tendu(e) et nerveux(se)", "dimension": "N", "facet": "Anxiété", "reverse": False},
            {"id": "N2", "text": "Je me mets facilement en colère", "dimension": "N", "facet": "Hostilité", "reverse": False},
            {"id": "N3", "text": "Je me sens souvent triste et mélancolique", "dimension": "N", "facet": "Dépression", "reverse": False},
            {"id": "N4", "text": "Je me sens mal à l'aise avec les autres", "dimension": "N", "facet": "Timidité sociale", "reverse": False},
            {"id": "N5", "text": "J'agis souvent sur un coup de tête", "dimension": "N", "facet": "Impulsivité", "reverse": False},
            {"id": "N6", "text": "Je me sens souvent submergé(e) par les événements", "dimension": "N", "facet": "Vulnérabilité", "reverse": False},
            {"id": "N7", "text": "Je suis rarement inquiet(e)", "dimension": "N", "facet": "Anxiété", "reverse": True},
            {"id": "N8", "text": "Je reste calme même dans des situations frustrantes", "dimension": "N", "facet": "Hostilité", "reverse": True},
            {"id": "N9", "text": "Je me sens généralement de bonne humeur", "dimension": "N", "facet": "Dépression", "reverse": True},
            {"id": "N10", "text": "J'ai confiance en moi dans les situations sociales", "dimension": "N", "facet": "Timidité sociale", "reverse": True},
            {"id": "N11", "text": "Je réfléchis avant d'agir", "dimension": "N", "facet": "Impulsivité", "reverse": True},
            {"id": "N12", "text": "Je gère bien le stress", "dimension": "N", "facet": "Vulnérabilité", "reverse": True},

            # Extraversion (E1-E12)
            {"id": "E1", "text": "J'aime être entouré(e) de beaucoup de monde", "dimension": "E", "facet": "Grégarité", "reverse": False},
            {"id": "E2", "text": "Je me fais facilement des amis", "dimension": "E", "facet": "Chaleur", "reverse": False},
            {"id": "E3", "text": "Je n'hésite pas à prendre la parole en groupe", "dimension": "E", "facet": "Assertivité", "reverse": False},
            {"id": "E4", "text": "J'aime que les choses bougent autour de moi", "dimension": "E", "facet": "Activité", "reverse": False},
            {"id": "E5", "text": "J'aime les sensations fortes", "dimension": "E", "facet": "Recherche de sensations", "reverse": False},
            {"id": "E6", "text": "Je me sens souvent joyeux(se) et enthousiaste", "dimension": "E", "facet": "Émotions positives", "reverse": False},
            {"id": "E7", "text": "Je préfère être seul(e)", "dimension": "E", "facet": "Grégarité", "reverse": True},
            {"id": "E8", "text": "J'ai du mal à m'ouvrir aux autres", "dimension": "E", "facet": "Chaleur", "reverse": True},
            {"id": "E9", "text": "J'évite d'être le centre d'attention", "dimension": "E", "facet": "Assertivité", "reverse": True},
            {"id": "E10", "text": "Je préfère un rythme de vie tranquille", "dimension": "E", "facet": "Activité", "reverse": True},
            {"id": "E11", "text": "J'évite les situations risquées", "dimension": "E", "facet": "Recherche de sensations", "reverse": True},
            {"id": "E12", "text": "Je ne suis pas quelqu'un de très enjoué", "dimension": "E", "facet": "Émotions positives", "reverse": True},

            # Ouverture (O1-O12)
            {"id": "O1", "text": "J'ai une imagination très vive", "dimension": "O", "facet": "Fantaisie", "reverse": False},
            {"id": "O2", "text": "J'apprécie l'art et la beauté", "dimension": "O", "facet": "Esthétique", "reverse": False},
            {"id": "O3", "text": "Je ressens intensément mes émotions", "dimension": "O", "facet": "Sentiments", "reverse": False},
            {"id": "O4", "text": "J'aime essayer de nouvelles activités", "dimension": "O", "facet": "Actions", "reverse": False},
            {"id": "O5", "text": "J'aime réfléchir à des concepts abstraits", "dimension": "O", "facet": "Idées", "reverse": False},
            {"id": "O6", "text": "Je remets en question les valeurs traditionnelles", "dimension": "O", "facet": "Valeurs", "reverse": False},
            {"id": "O7", "text": "Je ne suis pas très créatif(ve)", "dimension": "O", "facet": "Fantaisie", "reverse": True},
            {"id": "O8", "text": "L'art me laisse indifférent(e)", "dimension": "O", "facet": "Esthétique", "reverse": True},
            {"id": "O9", "text": "Je contrôle bien mes émotions", "dimension": "O", "facet": "Sentiments", "reverse": True},
            {"id": "O10", "text": "Je préfère la routine au changement", "dimension": "O", "facet": "Actions", "reverse": True},
            {"id": "O11", "text": "Je ne m'intéresse pas aux discussions philosophiques", "dimension": "O", "facet": "Idées", "reverse": True},
            {"id": "O12", "text": "Je respecte les traditions établies", "dimension": "O", "facet": "Valeurs", "reverse": True},

            # Agréabilité (A1-A12)
            {"id": "A1", "text": "Je fais facilement confiance aux autres", "dimension": "A", "facet": "Confiance", "reverse": False},
            {"id": "A2", "text": "Je suis honnête et sincère", "dimension": "A", "facet": "Droiture", "reverse": False},
            {"id": "A3", "text": "J'aime aider les autres", "dimension": "A", "facet": "Altruisme", "reverse": False},
            {"id": "A4", "text": "J'évite les conflits", "dimension": "A", "facet": "Compliance", "reverse": False},
            {"id": "A5", "text": "Je ne me vante pas de mes réussites", "dimension": "A", "facet": "Modestie", "reverse": False},
            {"id": "A6", "text": "Je suis sensible aux émotions des autres", "dimension": "A", "facet": "Sensibilité", "reverse": False},
            {"id": "A7", "text": "Je me méfie des intentions des autres", "dimension": "A", "facet": "Confiance", "reverse": True},
            {"id": "A8", "text": "Il m'arrive de manipuler les autres", "dimension": "A", "facet": "Droiture", "reverse": True},
            {"id": "A9", "text": "Je pense d'abord à moi", "dimension": "A", "facet": "Altruisme", "reverse": True},
            {"id": "A10", "text": "Je n'hésite pas à imposer mon point de vue", "dimension": "A", "facet": "Compliance", "reverse": True},
            {"id": "A11", "text": "Je pense mériter plus que les autres", "dimension": "A", "facet": "Modestie", "reverse": True},
            {"id": "A12", "text": "Les problèmes des autres ne me touchent pas", "dimension": "A", "facet": "Sensibilité", "reverse": True},

            # Conscienciosité (C1-C12)
            {"id": "C1", "text": "Je me sens capable de faire face à la plupart des situations", "dimension": "C", "facet": "Compétence", "reverse": False},
            {"id": "C2", "text": "J'aime que tout soit bien organisé", "dimension": "C", "facet": "Ordre", "reverse": False},
            {"id": "C3", "text": "Je respecte mes engagements", "dimension": "C", "facet": "Sens du devoir", "reverse": False},
            {"id": "C4", "text": "Je me fixe des objectifs élevés", "dimension": "C", "facet": "Recherche de réussite", "reverse": False},
            {"id": "C5", "text": "J'ai une grande force de volonté", "dimension": "C", "facet": "Autodiscipline", "reverse": False},
            {"id": "C6", "text": "Je réfléchis longuement avant de prendre une décision", "dimension": "C", "facet": "Délibération", "reverse": False},
            {"id": "C7", "text": "Je doute souvent de mes capacités", "dimension": "C", "facet": "Compétence", "reverse": True},
            {"id": "C8", "text": "Je suis plutôt désordonné(e)", "dimension": "C", "facet": "Ordre", "reverse": True},
            {"id": "C9", "text": "Il m'arrive de ne pas tenir mes promesses", "dimension": "C", "facet": "Sens du devoir", "reverse": True},
            {"id": "C10", "text": "Je me contente facilement de ce que j'ai", "dimension": "C", "facet": "Recherche de réussite", "reverse": True},
            {"id": "C11", "text": "J'ai du mal à me contrôler", "dimension": "C", "facet": "Autodiscipline", "reverse": True},
            {"id": "C12", "text": "Je prends souvent des décisions hâtives", "dimension": "C", "facet": "Délibération", "reverse": True},
        ]

    def calculate_scores(self, responses):
        """Calcule les scores pour chaque dimension et facette"""
        scores = {dim: 0 for dim in self.dimensions.keys()}
        facet_scores = {dim: {facet: 0 for facet in self.facets[dim]} for dim in self.dimensions.keys()}

        for question in self.questions:
            question_id = question['id']
            if question_id in responses:
                response = responses[question_id]

                # Inversion si nécessaire
                if question['reverse']:
                    score = 6 - response  # Échelle 1-5 inversée
                else:
                    score = response

                dimension = question['dimension']
                facet = question['facet']

                scores[dimension] += score
                facet_scores[dimension][facet] += score

        # Conversion en percentiles (approximatifs)
        percentiles = {}
        for dim in scores:
            # Normalisation approximative (à ajuster avec vraies normes)
            raw_score = scores[dim]
            max_possible = 12 * 5  # 12 questions par dimension, échelle 1-5
            percentile = min(100, max(0, (raw_score / max_possible) * 100))
            percentiles[dim] = percentile

        return scores, facet_scores, percentiles

    def get_interpretation(self, percentiles):
        """Fournit une interprétation des scores"""
        interpretations = {}

        for dim, percentile in percentiles.items():
            if percentile >= 70:
                level = "Élevé"
            elif percentile >= 30:
                level = "Moyen"
            else:
                level = "Faible"

            interpretations[dim] = {
                'level': level,
                'percentile': percentile,
                'description': self.get_dimension_description(dim, level)
            }

        return interpretations

    def get_dimension_description(self, dimension, level):
        """Retourne une description détaillée de chaque dimension selon le niveau"""
        descriptions = {
            'N': {
                'Élevé': "Vous avez tendance à éprouver plus souvent des émotions négatives comme l'anxiété, la tristesse ou la colère. Vous pouvez être plus sensible au stress.",
                'Moyen': "Vous maintenez un équilibre émotionnel relatif, avec des périodes de stress normal alternant avec des moments de sérénité.",
                'Faible': "Vous êtes généralement calme, serein et émotionnellement stable. Vous gérez bien le stress et restez optimiste."
            },
            'E': {
                'Élevé': "Vous êtes sociable, énergique et aimez être entouré. Vous cherchez la stimulation et êtes souvent de bonne humeur.",
                'Moyen': "Vous appréciez la compagnie des autres tout en valorisant aussi les moments de solitude. Votre niveau d'énergie est équilibré.",
                'Faible': "Vous préférez les interactions en petit groupe ou la solitude. Vous êtes plus réservé et réfléchi dans vos actions."
            },
            'O': {
                'Élevé': "Vous êtes créatif, curieux et ouvert aux nouvelles expériences. Vous appréciez l'art, les idées abstraites et le changement.",
                'Moyen': "Vous montrez un intérêt modéré pour les nouvelles expériences, combinant ouverture et pragmatisme.",
                'Faible': "Vous préférez la familiarité et les méthodes éprouvées. Vous êtes pragmatique et moins attiré par l'abstraction."
            },
            'A': {
                'Élevé': "Vous êtes coopératif, confiant et bienveillant envers les autres. Vous évitez les conflits et cherchez l'harmonie.",
                'Moyen': "Vous équilibrez coopération et compétition, confiance et prudence selon les situations.",
                'Faible': "Vous êtes plus compétitif et sceptique. Vous défendez vos intérêts et pouvez être plus direct dans vos interactions."
            },
            'C': {
                'Élevé': "Vous êtes organisé, discipliné et persévérant. Vous planifiez soigneusement et atteignez vos objectifs méthodiquement.",
                'Moyen': "Vous trouvez un équilibre entre organisation et flexibilité, planification et spontanéité.",
                'Faible': "Vous êtes plus flexible et spontané. Vous préférez vous adapter aux situations plutôt que de tout planifier."
            }
        }

        return descriptions.get(dimension, {}).get(level, "Description non disponible")

# ================= FONCTIONS UTILITAIRES =================

def hash_user_data(data: str) -> str:
    """Hache les données utilisateur pour la sécurité"""
    return hashlib.sha256(data.encode()).hexdigest()

def initialize_session_state():
    """Initialise l'état de session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_session_id = str(uuid.uuid4())
        st.session_state.session_start = datetime.now()
        st.session_state.tool_choice = "🏠 Accueil"
        st.session_state.test_started = False
        st.session_state.test_completed = False
        st.session_state.responses = {}
        st.session_state.current_question = 0
        st.session_state.scores = {}
        st.session_state.interpretations = {}

def set_custom_theme():
    """Applique le thème personnalisé inspiré du site de référence"""
    css_theme = """
    <style>
    /* Variables globales */
    :root {
        --primary: #2c3e50 !important;
        --secondary: #3498db !important;
        --accent: #e74c3c !important;
        --background: #f8f9fa !important;
        --sidebar-bg: #ffffff !important;
        --sidebar-border: #e9ecef !important;
        --text-primary: #2c3e50 !important;
        --text-secondary: #6c757d !important;
        --sidebar-width-collapsed: 60px !important;
        --sidebar-width-expanded: 240px !important;
        --sidebar-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        --shadow-light: 0 2px 8px rgba(0,0,0,0.08) !important;
        --shadow-medium: 0 4px 16px rgba(0,0,0,0.12) !important;
    }

    /* Structure principale */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background) !important;
    }

    /* Sidebar compacte */
    [data-testid="stSidebar"] {
        width: var(--sidebar-width-collapsed) !important;
        min-width: var(--sidebar-width-collapsed) !important;
        max-width: var(--sidebar-width-collapsed) !important;
        height: 100vh !important;
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        z-index: 999999 !important;
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--sidebar-border) !important;
        box-shadow: var(--shadow-light) !important;
        overflow: hidden !important;
        padding: 0 !important;
        transition: var(--sidebar-transition) !important;
    }

    [data-testid="stSidebar"]:hover {
        width: var(--sidebar-width-expanded) !important;
        min-width: var(--sidebar-width-expanded) !important;
        max-width: var(--sidebar-width-expanded) !important;
        box-shadow: var(--shadow-medium) !important;
        overflow-y: auto !important;
    }

    [data-testid="stSidebar"] > div {
        width: var(--sidebar-width-expanded) !important;
        padding: 12px 8px !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    [data-testid="stSidebar"]:hover > div {
        overflow-y: auto !important;
        padding: 16px 12px !important;
    }

    /* En-tête de la sidebar */
    [data-testid="stSidebar"] h2 {
        font-size: 0 !important;
        margin: 0 0 20px 0 !important;
        padding: 12px 0 !important;
        border-bottom: 1px solid var(--sidebar-border) !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        height: 60px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stSidebar"] h2::before {
        content: "🧠" !important;
        font-size: 28px !important;
        display: block !important;
        margin: 0 !important;
    }

    [data-testid="stSidebar"]:hover h2 {
        font-size: 1.4rem !important;
        color: var(--primary) !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"]:hover h2::before {
        font-size: 20px !important;
        margin-right: 8px !important;
    }

    /* Options de navigation */
    [data-testid="stSidebar"] .stRadio {
        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
        padding: 0 !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        display: flex !important;
        align-items: center !important;
        padding: 10px 6px !important;
        margin: 0 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        position: relative !important;
        height: 44px !important;
        overflow: hidden !important;
        background: transparent !important;
    }

    [data-testid="stSidebar"] .stRadio label > div:first-child {
        display: none !important;
    }

    [data-testid="stSidebar"] .stRadio label span {
        font-size: 0 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        text-align: center !important;
        position: relative !important;
    }

    [data-testid="stSidebar"] .stRadio label span::before {
        font-size: 22px !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }

    /* Icônes pour chaque option */
    [data-testid="stSidebar"] .stRadio label:nth-child(1) span::before { content: "🏠" !important; }
    [data-testid="stSidebar"] .stRadio label:nth-child(2) span::before { content: "📝" !important; }
    [data-testid="stSidebar"] .stRadio label:nth-child(3) span::before { content: "📊" !important; }
    [data-testid="stSidebar"] .stRadio label:nth-child(4) span::before { content: "ℹ️" !important; }

    /* Mode étendu */
    [data-testid="stSidebar"]:hover .stRadio label span {
        font-size: 14px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding-left: 12px !important;
    }

    [data-testid="stSidebar"]:hover .stRadio label span::before {
        font-size: 18px !important;
        position: absolute !important;
        left: -8px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: auto !important;
    }

    /* Effets de survol */
    [data-testid="stSidebar"] .stRadio label:hover {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef) !important;
        transform: translateX(3px) !important;
        box-shadow: var(--shadow-light) !important;
    }

    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        background: linear-gradient(135deg, var(--secondary), #2980b9) !important;
        color: white !important;
        box-shadow: var(--shadow-medium) !important;
    }

    /* Contenu principal */
    .main .block-container {
        margin-left: calc(var(--sidebar-width-collapsed) + 16px) !important;
        padding: 1.5rem !important;
        max-width: calc(100vw - var(--sidebar-width-collapsed) - 32px) !important;
        transition: var(--sidebar-transition) !important;
    }

    /* Boutons stylisés */
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary), #2980b9) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-light) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-medium) !important;
        background: linear-gradient(135deg, #2980b9, var(--secondary)) !important;
    }

    /* Cards d'information */
    .info-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #3498db;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    /* Questions du test */
    .question-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2ecc71;
    }

    /* Responsive */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            transform: translateX(-100%) !important;
        }

        [data-testid="stSidebar"]:hover {
            transform: translateX(0) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
        }

        .main .block-container {
            margin-left: 0 !important;
            max-width: 100vw !important;
            padding: 1rem !important;
        }
    }
    </style>
    """

    st.markdown(css_theme, unsafe_allow_html=True)

@st.cache_data
def create_personality_chart(scores, interpretations):
    """Crée un graphique radar de la personnalité"""
    dimensions = list(scores.keys())
    values = [interpretations[dim]['percentile'] for dim in dimensions]

    # Ajout du premier point à la fin pour fermer le radar
    dimensions_radar = dimensions + [dimensions[0]]
    values_radar = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_radar,
        theta=dimensions_radar,
        fill='toself',
        name='Votre profil',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line=dict(color='#3498db', width=3)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                ticktext=['20%', '40%', '60%', '80%', '100%']
            )
        ),
        showlegend=False,
        title="Votre Profil de Personnalité NEO PI-R",
        title_x=0.5,
        height=500
    )

    return fig

@st.cache_data
def create_facet_chart(facet_scores, dimension):
    """Crée un graphique des facettes pour une dimension"""
    facets = list(facet_scores[dimension].keys())
    values = list(facet_scores[dimension].values())

    fig = px.bar(
        x=values,
        y=facets,
        orientation='h',
        title=f"Facettes de {dimension}",
        labels={'x': 'Score', 'y': 'Facettes'},
        color=values,
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        coloraxis_showscale=False
    )

    return fig

# ================= PAGES DE L'APPLICATION =================

def show_navigation_menu():
    """Menu de navigation principal"""
    st.markdown("## 🧠 NEO PI-R - Navigation")
    st.markdown("Choisissez une section :")

    options = [
        "🏠 Accueil",
        "📝 Passer le Test",
        "📊 Résultats",
        "ℹ️ À propos"
    ]

    if 'tool_choice' not in st.session_state or st.session_state.tool_choice not in options:
        st.session_state.tool_choice = "🏠 Accueil"

    current_index = options.index(st.session_state.tool_choice)

    tool_choice = st.radio(
        "",
        options,
        label_visibility="collapsed",
        index=current_index,
        key="main_navigation"
    )

    if tool_choice != st.session_state.tool_choice:
        st.session_state.tool_choice = tool_choice

    return tool_choice

def show_home_page():
    """Page d'accueil du test NEO PI-R"""
    # En-tête principal
    st.markdown("""
    <div style="background: linear-gradient(90deg, #3498db, #2ecc71);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            🧠 Test de Personnalité NEO PI-R
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Découvrez votre profil de personnalité avec l'un des tests les plus fiables de la psychologie
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section "Qu'est-ce que le NEO PI-R ?"
    st.markdown("""
    <div class="info-card">
        <h2 style="color: #3498db; margin-bottom: 25px; font-size: 2.2rem; text-align: center;">
            🔬 Qu'est-ce que le NEO PI-R ?
        </h2>
        <p style="font-size: 1.2rem; line-height: 1.8; text-align: justify;
                  max-width: 900px; margin: 0 auto; color: #2c3e50;">
            Le <strong>NEO PI-R (NEO Personality Inventory-Revised)</strong> est l'un des outils de mesure
            de la personnalité les plus utilisés et respectés en psychologie. Développé par Paul Costa et
            Robert McCrae, ce test évalue votre personnalité selon le modèle des <strong>Big Five</strong>,
            considéré comme la référence internationale en matière de traits de personnalité.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Les 5 dimensions principales
    st.markdown("""
    <h2 style="color: #3498db; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        🌟 Les Cinq Grandes Dimensions de la Personnalité
    </h2>
    """, unsafe_allow_html=True)

    # Grille des dimensions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e74c3c, #c0392b);
                   color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; height: 200px;">
            <h3 style="margin-top: 0; display: flex; align-items: center;">
                <span style="margin-right: 10px;">😰</span>
                Neuroticisme (N)
            </h3>
            <p style="line-height: 1.6; font-size: 0.95rem;">
                Tendance à éprouver des émotions négatives comme l'anxiété, la dépression,
                l'hostilité. Mesure votre stabilité émotionnelle et votre gestion du stress.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #2ecc71, #27ae60);
                   color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; height: 200px;">
            <h3 style="margin-top: 0; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🎨</span>
                Ouverture (O)
            </h3>
            <p style="line-height: 1.6; font-size: 0.95rem;">
                Ouverture aux expériences nouvelles, à l'imagination, à l'art, aux émotions,
                aux idées et aux valeurs non conventionnelles.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #9b59b6, #8e44ad);
                   color: white; padding: 25px; border-radius: 15px; height: 200px;">
            <h3 style="margin-top: 0; display: flex; align-items: center;">
                <span style="margin-right: 10px;">📋</span>
                Conscienciosité (C)
            </h3>
            <p style="line-height: 1.6; font-size: 0.95rem;">
                Organisation, persévérance, contrôle des impulses et orientation vers les objectifs.
                Mesure votre autodiscipline et votre fiabilité.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f39c12, #e67e22);
                   color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; height: 200px;">
            <h3 style="margin-top: 0; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🎉</span>
                Extraversion (E)
            </h3>
            <p style="line-height: 1.6; font-size: 0.95rem;">
                Niveau d'activité sociale, d'assertivité, d'émotions positives et de recherche
                de stimulation. Mesure votre sociabilité et votre énergie.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #3498db, #2980b9);
                   color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; height: 200px;">
            <h3 style="margin-top: 0; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🤝</span>
                Agréabilité (A)
            </h3>
            <p style="line-height: 1.6; font-size: 0.95rem;">
                Coopération, confiance, altruisme et tendance à éviter les conflits.
                Mesure votre bienveillance envers les autres.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Section utilité du test
    st.markdown("""
    <h2 style="color: #3498db; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        🎯 Pourquoi passer ce test ?
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    benefits = [
        {
            "title": "🔍 Connaissance de soi",
            "items": ["Comprendre vos traits dominants", "Identifier vos forces et défis", "Mieux vous connaître", "Développement personnel"],
            "gradient": "linear-gradient(135deg, #3498db, #2980b9)"
        },
        {
            "title": "💼 Orientation professionnelle",
            "items": ["Métiers adaptés à votre profil", "Style de management", "Environnement de travail", "Évolution de carrière"],
            "gradient": "linear-gradient(135deg, #2ecc71, #27ae60)"
        },
        {
            "title": "👥 Relations interpersonnelles",
            "items": ["Améliorer vos relations", "Comprendre les autres", "Communication efficace", "Résolution de conflits"],
            "gradient": "linear-gradient(135deg, #9b59b6, #8e44ad)"
        }
    ]

    for i, (benefit, col) in enumerate(zip(benefits, [col1, col2, col3])):
        with col:
            items_html = "".join([f"<li>{item}</li>" for item in benefit['items']])
            st.markdown(f"""
            <div style="background: {benefit['gradient']}; color: white;
                       padding: 25px; border-radius: 15px; height: 280px;
                       box-shadow: 0 6px 20px rgba(0,0,0,0.15);">
                <h3 style="border-bottom: 2px solid rgba(255,255,255,0.3);
                          padding-bottom: 12px; margin-bottom: 20px; font-size: 1.3rem;">
                    {benefit['title']}
                </h3>
                <ul style="padding-left: 20px; margin: 0; line-height: 1.8;">
                    {items_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # Section fonctionnement
    st.markdown("""
    <h2 style="color: #3498db; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        ⚙️ Comment fonctionne le test ?
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #3498db; margin-top: 0;">📝 60 Questions</h4>
                <p style="color: #2c3e50; margin: 0;">Questions soigneusement sélectionnées pour évaluer chaque dimension</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #3498db; margin-top: 0;">⏱️ 10-15 minutes</h4>
                <p style="color: #2c3e50; margin: 0;">Durée moyenne pour compléter le test en toute sérénité</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #3498db; margin-top: 0;">📊 Analyse détaillée</h4>
                <p style="color: #2c3e50; margin: 0;">Résultats complets avec interprétations personnalisées</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #3498db; margin-top: 0;">🔒 Confidentialité</h4>
                <p style="color: #2c3e50; margin: 0;">Vos données restent privées et sécurisées</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("""
    <h2 style="color: #3498db; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        📋 Instructions pour le test
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <div style="background: #e8f4fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #2c3e50; margin-top: 0;">🎯 Conseils pour obtenir des résultats précis</h4>
            <ul style="color: #34495e; padding-left: 25px; line-height: 1.8;">
                <li><strong>Soyez honnête</strong> : Répondez selon ce que vous êtes vraiment, pas selon ce que vous aimeriez être</li>
                <li><strong>Première impression</strong> : Choisissez la réponse qui vous vient spontanément à l'esprit</li>
                <li><strong>Pas de "bonne" réponse</strong> : Il n'y a pas de profil idéal, chaque personnalité a ses forces</li>
                <li><strong>Contexte général</strong> : Pensez à votre comportement habituel, pas à des situations exceptionnelles</li>
                <li><strong>Prenez votre temps</strong> : Mais ne réfléchissez pas trop longtemps à chaque question</li>
            </ul>
        </div>

        <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #856404; margin-top: 0;">⚠️ Important à savoir</h4>
            <ul style="color: #856404; padding-left: 25px; line-height: 1.8;">
                <li>Ce test est à des fins éducatives et de développement personnel</li>
                <li>Il ne remplace pas une évaluation psychologique professionnelle</li>
                <li>Vos résultats peuvent évoluer avec le temps et les expériences</li>
                <li>Toutes les dimensions de personnalité ont leur valeur</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton pour commencer
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Commencer le Test NEO PI-R", type="primary", use_container_width=True):
            st.session_state.tool_choice = "📝 Passer le Test"
            st.session_state.test_started = True
            st.rerun()

    # Footer
    st.markdown("""
    <div style="margin: 40px 0 30px 0; padding: 20px; border-radius: 12px;
               border-left: 4px solid #3498db; background: linear-gradient(135deg, #f8f9fa, #e9ecef);
               box-shadow: 0 4px 12px rgba(52, 152, 219, 0.1);">
        <p style="font-size: 1rem; color: #2c3e50; text-align: center; margin: 0; line-height: 1.6;">
            <strong style="color: #3498db;">💡 Bon à savoir :</strong>
            Le modèle des Big Five est utilisé dans de nombreux domaines : recrutement, coaching,
            recherche en psychologie, et développement personnel.
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_test_page():
    """Page du test NEO PI-R"""
    neo_manager = NEOPIRManager()

    if not st.session_state.test_started:
        st.session_state.test_started = True
        st.session_state.current_question = 0
        st.session_state.responses = {}

    total_questions = len(neo_manager.questions)
    progress = st.session_state.current_question / total_questions

    # En-tête avec progression
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3498db, #2ecc71);
                padding: 30px 25px; border-radius: 20px; margin-bottom: 25px; text-align: center;">
        <h1 style="color: white; font-size: 2.5rem; margin-bottom: 10px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            📝 Test NEO PI-R en cours
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.1rem; margin: 0;">
            Question {st.session_state.current_question + 1} sur {total_questions}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Barre de progression
    st.progress(progress)

    if st.session_state.current_question < total_questions:
        # Question actuelle
        current_q = neo_manager.questions[st.session_state.current_question]

        # Affichage de la question
        st.markdown(f"""
        <div class="question-card">
            <h3 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.4rem;">
                Question {st.session_state.current_question + 1} / {total_questions}
            </h3>
            <p style="font-size: 1.2rem; line-height: 1.6; color: #34495e; margin-bottom: 25px;">
                <strong>{current_q['text']}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Options de réponse
        st.markdown("### Votre réponse :")

        response_options = [
            "Pas du tout d'accord",
            "Plutôt pas d'accord",
            "Ni d'accord ni pas d'accord",
            "Plutôt d'accord",
            "Tout à fait d'accord"
        ]

        # Récupération de la réponse précédente si elle existe
        previous_response = st.session_state.responses.get(current_q['id'], None)
        default_index = previous_response - 1 if previous_response else 0

        response = st.radio(
            "Choisissez votre niveau d'accord :",
            response_options,
            index=default_index,
            key=f"question_{current_q['id']}",
            label_visibility="collapsed"
        )

        # Conversion en score numérique
        response_score = response_options.index(response) + 1
        st.session_state.responses[current_q['id']] = response_score

        # Boutons de navigation
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            if st.session_state.current_question > 0:
                if st.button("⬅️ Question précédente", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()

        with col3:
            if st.session_state.current_question < total_questions - 1:
                if st.button("Question suivante ➡️", type="primary", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("🎯 Terminer le test", type="primary", use_container_width=True):
                    # Calcul des scores
                    scores, facet_scores, percentiles = neo_manager.calculate_scores(st.session_state.responses)
                    interpretations = neo_manager.get_interpretation(percentiles)

                    # Sauvegarde des résultats
                    st.session_state.scores = scores
                    st.session_state.facet_scores = facet_scores
                    st.session_state.percentiles = percentiles
                    st.session_state.interpretations = interpretations
                    st.session_state.test_completed = True

                    # Redirection vers les résultats
                    st.session_state.tool_choice = "📊 Résultats"
                    st.rerun()

        # Informations sur la dimension actuelle
        dimension = current_q['dimension']
        dimension_name = neo_manager.dimensions[dimension]
        facet = current_q['facet']

        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <p style="color: #6c757d; margin: 0; text-align: center;">
                <strong>Dimension évaluée :</strong> {dimension_name} ({dimension}) - Facette : {facet}
            </p>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Test terminé
        st.success("🎉 Test terminé ! Redirection vers vos résultats...")
        time.sleep(2)
        st.session_state.tool_choice = "📊 Résultats"
        st.rerun()

def show_results_page():
    """Page des résultats du test NEO PI-R"""
    if not st.session_state.test_completed:
        st.warning("⚠️ Vous devez d'abord passer le test pour voir vos résultats.")
        if st.button("📝 Passer le test"):
            st.session_state.tool_choice = "📝 Passer le Test"
            st.rerun()
        return

    neo_manager = NEOPIRManager()

    # En-tête des résultats
    st.markdown("""
    <div style="background: linear-gradient(90deg, #27ae60, #2ecc71);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            📊 Vos Résultats NEO PI-R
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Découvrez votre profil de personnalité unique
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs pour organiser les résultats
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Vue d'ensemble",
        "📈 Profil détaillé",
        "🔍 Analyse par dimension",
        "💡 Recommandations"
    ])

    with tab1:
        # Vue d'ensemble du profil
        st.markdown("## 🎯 Votre Profil de Personnalité")

        # Graphique radar
        fig_radar = create_personality_chart(st.session_state.scores, st.session_state.interpretations)
        st.plotly_chart(fig_radar, use_container_width=True)

        # Résumé des scores
        st.markdown("### 📊 Vos Scores par Dimension")

        # Création du tableau de scores
        results_data = []
        for dim in ['N', 'E', 'O', 'A', 'C']:
            dim_name = neo_manager.dimensions[dim]
            interp = st.session_state.interpretations[dim]
            results_data.append({
                'Dimension': f"{dim_name} ({dim})",
                'Percentile': f"{interp['percentile']:.0f}%",
                'Niveau': interp['level'],
                'Score brut': st.session_state.scores[dim]
            })

        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True, hide_index=True)

        # Interprétation générale
        st.markdown("### 🔍 Interprétation Générale")

        # Identification du trait dominant
        max_percentile = max(st.session_state.percentiles.values())
        dominant_dim = [dim for dim, perc in st.session_state.percentiles.items() if perc == max_percentile][0]
        dominant_name = neo_manager.dimensions[dominant_dim]

        # Identification du trait le plus faible
        min_percentile = min(st.session_state.percentiles.values())
        lowest_dim = [dim for dim, perc in st.session_state.percentiles.items() if perc == min_percentile][0]
        lowest_name = neo_manager.dimensions[lowest_dim]

        st.markdown(f"""
        <div class="info-card">
            <h4 style="color: #2c3e50; margin-top: 0;">🌟 Votre profil en un coup d'œil</h4>
            <p style="color: #34495e; line-height: 1.6;">
                Votre trait de personnalité le plus marqué est <strong>{dominant_name}</strong>
                ({max_percentile:.0f}e percentile), ce qui suggère que {st.session_state.interpretations[dominant_dim]['description'].lower()}
            </p>
            <p style="color: #34495e; line-height: 1.6;">
                Votre score le plus modéré concerne <strong>{lowest_name}</strong>
                ({min_percentile:.0f}e percentile), indiquant que {st.session_state.interpretations[lowest_dim]['description'].lower()}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        # Profil détaillé avec graphiques
        st.markdown("## 📈 Analyse Détaillée de Votre Profil")

        # Graphique en barres des percentiles
        dimensions = list(neo_manager.dimensions.values())
        percentiles = [st.session_state.percentiles[dim] for dim in ['N', 'E', 'O', 'A', 'C']]

        fig_bar = px.bar(
            x=dimensions,
            y=percentiles,
            title="Vos Percentiles par Dimension",
            labels={'x': 'Dimensions', 'y': 'Percentile'},
            color=percentiles,
            color_continuous_scale='RdYlBu_r'
        )

        fig_bar.add_hline(y=50, line_dash="dash", line_color="gray",
                         annotation_text="Moyenne (50e percentile)")
        fig_bar.add_hline(y=70, line_dash="dash", line_color="red",
                         annotation_text="Niveau élevé (70e percentile)")
        fig_bar.add_hline(y=30, line_dash="dash", line_color="blue",
                         annotation_text="Niveau faible (30e percentile)")

        fig_bar.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Comparaison avec la population générale
        st.markdown("### 👥 Comparaison avec la Population Générale")

        col1, col2 = st.columns(2)

        with col1:
            # Graphique de distribution normale
            fig_dist = go.Figure()

            x = np.linspace(0, 100, 100)
            y = stats.norm.pdf(x, 50, 15)  # Distribution normale centrée sur 50

            fig_dist.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                name='Population générale',
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.3)',
                line=dict(color='#3498db')
            ))

            # Ajout des positions du participant
            for dim in ['N', 'E', 'O', 'A', 'C']:
                percentile = st.session_state.percentiles[dim]
                y_pos = stats.norm.pdf(percentile, 50, 15)
                fig_dist.add_trace(go.Scatter(
                    x=[percentile],
                    y=[y_pos],
                    mode='markers',
                    name=neo_manager.dimensions[dim],
                    marker=dict(size=12)
                ))

            fig_dist.update_layout(
                title="Votre Position dans la Distribution",
                xaxis_title="Percentile",
                yaxis_title="Densité",
                height=400
            )

            st.plotly_chart(fig_dist, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Répartition de vos scores")

            # Comptage par niveau
            levels_count = {'Élevé': 0, 'Moyen': 0, 'Faible': 0}
            for interp in st.session_state.interpretations.values():
                levels_count[interp['level']] += 1

            fig_pie = px.pie(
                values=list(levels_count.values()),
                names=list(levels_count.keys()),
                title="Répartition de vos niveaux",
                color_discrete_map={'Élevé': '#e74c3c', 'Moyen': '#f39c12', 'Faible': '#3498db'}
            )

            st.plotly_chart(fig_pie, use_container_width=True)

            # Métriques
            st.metric("Traits élevés", levels_count['Élevé'],
                     f"{levels_count['Élevé']}/5 dimensions")
            st.metric("Traits moyens", levels_count['Moyen'],
                     f"{levels_count['Moyen']}/5 dimensions")
            st.metric("Traits faibles", levels_count['Faible'],
                     f"{levels_count['Faible']}/5 dimensions")

    with tab3:
        # Analyse détaillée par dimension
        st.markdown("## 🔍 Analyse Approfondie par Dimension")

        # Sélecteur de dimension
        selected_dim = st.selectbox(
            "Choisissez une dimension à analyser en détail :",
            options=['N', 'E', 'O', 'A', 'C'],
            format_func=lambda x: f"{neo_manager.dimensions[x]} ({x})",
            key="dimension_selector"
        )

        interp = st.session_state.interpretations[selected_dim]
        dim_name = neo_manager.dimensions[selected_dim]

        # En-tête de la dimension
        level_color = {'Élevé': '#e74c3c', 'Moyen': '#f39c12', 'Faible': '#3498db'}[interp['level']]

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {level_color}, {level_color}dd);
                   color: white; padding: 30px; border-radius: 15px; margin-bottom: 25px;">
            <h2 style="margin: 0 0 15px 0; font-size: 2rem;">
                {dim_name} ({selected_dim})
            </h2>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; font-size: 1.5rem;">Niveau : {interp['level']}</h3>
                    <p style="margin: 5px 0 0 0; font-size: 1.1rem;">
                        {interp['percentile']:.0f}e percentile
                    </p>
                </div>
                <div style="font-size: 3rem; opacity: 0.7;">
                    {interp['percentile']:.0f}%
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Description détaillée
        st.markdown(f"""
        <div class="info-card">
            <h4 style="color: #2c3e50; margin-top: 0;">📝 Interprétation de votre score</h4>
            <p style="color: #34495e; line-height: 1.8; font-size: 1.1rem;">
                {interp['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Graphique des facettes
        if selected_dim in st.session_state.facet_scores:
            st.markdown("### 🔍 Analyse des Facettes")

            fig_facets = create_facet_chart(st.session_state.facet_scores, selected_dim)
            st.plotly_chart(fig_facets, use_container_width=True)

            # Explication des facettes
            st.markdown("#### 📚 Explication des Facettes")

            facets_descriptions = {
                'N': {
                    'Anxiété': "Tendance à s'inquiéter, à ressentir de la nervosité et de la tension",
                    'Hostilité': "Tendance à éprouver de la colère, de la frustration et de l'amertume",
                    'Dépression': "Tendance à se sentir triste, découragé et désespéré",
                    'Timidité sociale': "Tendance à se sentir mal à l'aise en présence d'autres personnes",
                    'Impulsivité': "Tendance à agir sans réfléchir aux conséquences",
                    'Vulnérabilité': "Tendance à se sentir incapable de gérer le stress"
                },
                'E': {
                    'Chaleur': "Capacité à établir des relations chaleureuses et amicales",
                    'Grégarité': "Préférence pour la compagnie des autres",
                    'Assertivité': "Tendance à être dominant, énergique et socialement visible",
                    'Activité': "Rythme de vie rapide et niveau d'énergie élevé",
                    'Recherche de sensations': "Besoin d'excitation et de stimulation",
                    'Émotions positives': "Tendance à éprouver de la joie, du bonheur et de l'optimisme"
                },
                'O': {
                    'Fantaisie': "Imagination active et vie intérieure riche",
                    'Esthétique': "Appréciation de l'art, de la beauté et de la poésie",
                    'Sentiments': "Réceptivité à ses propres émotions et celles des autres",
                    'Actions': "Volonté d'essayer de nouvelles activités et d'aller vers l'inconnu",
                    'Idées': "Curiosité intellectuelle et ouverture aux nouvelles idées",
                    'Valeurs': "Disposition à remettre en question les valeurs établies"
                },
                'A': {
                    'Confiance': "Disposition à croire que les autres sont honnêtes et bienveillants",
                    'Droiture': "Franchise et sincérité dans les relations avec autrui",
                    'Altruisme': "Préoccupation active pour le bien-être des autres",
                    'Compliance': "Tendance à éviter les conflits et à coopérer",
                    'Modestie': "Tendance à être humble et effacé",
                    'Sensibilité': "Attitude de sympathie et de compassion envers les autres"
                },
                'C': {
                    'Compétence': "Sentiment d'être capable, sensé et efficace",
                    'Ordre': "Tendance à être organisé, soigneux et bien structuré",
                    'Sens du devoir': "Respect des obligations sociales et morales",
                    'Recherche de réussite': "Effort pour exceller et réussir",
                    'Autodiscipline': "Capacité à persévérer dans des tâches difficiles",
                    'Délibération': "Tendance à réfléchir soigneusement avant d'agir"
                }
            }

            for facet, score in st.session_state.facet_scores[selected_dim].items():
                description = facets_descriptions[selected_dim][facet]
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;
                           border-left: 4px solid #3498db;">
                    <h5 style="color: #2c3e50; margin: 0 0 8px 0;">
                        {facet} (Score: {score})
                    </h5>
                    <p style="color: #6c757d; margin: 0; font-size: 0.95rem;">
                        {description}
                    </p>
                </div>
                """, unsafe_allow_html=True)

    with tab4:
        # Recommandations personnalisées
        st.markdown("## 💡 Recommandations Personnalisées")

        # Analyse des forces et défis
        forces = []
        defis = []

        for dim, interp in st.session_state.interpretations.items():
            dim_name = neo_manager.dimensions[dim]
            if interp['level'] == 'Élevé':
                if dim in ['E', 'O', 'A', 'C']:  # Traits généralement positifs quand élevés
                    forces.append(f"{dim_name} : {interp['description']}")
                else:  # Neuroticisme élevé peut être un défi
                    defis.append(f"{dim_name} : {interp['description']}")
            elif interp['level'] == 'Faible':
                if dim == 'N':  # Neuroticisme faible est généralement positif
                    forces.append(f"{dim_name} faible : {interp['description']}")
                else:
                    defis.append(f"{dim_name} : {interp['description']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌟 Vos Forces")
            if forces:
                for force in forces:
                    st.markdown(f"""
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 10px 0;
                               border-left: 4px solid #28a745;">
                        <p style="color: #155724; margin: 0; line-height: 1.5;">
                            ✅ {force}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Votre profil présente un équilibre dans toutes les dimensions.")

        with col2:
            st.markdown("### 🎯 Axes de Développement")
            if defis:
                for defi in defis:
                    st.markdown(f"""
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;
                               border-left: 4px solid #ffc107;">
                        <p style="color: #856404; margin: 0; line-height: 1.5;">
                            🔄 {defi}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Votre profil ne présente pas d'axes de développement particuliers.")

        # Recommandations par domaine
        st.markdown("### 🎯 Recommandations par Domaine de Vie")

        # Carrière professionnelle
        career_recommendations = {
            'N': {
                'Élevé': "Envisagez des environnements de travail structurés et prévisibles. Les métiers d'aide peuvent vous convenir.",
                'Faible': "Vous pourriez exceller dans des postes à haute responsabilité ou des environnements stressants."
            },
            'E': {
                'Élevé': "Les métiers commerciaux, de management ou de relations publiques pourraient vous épanouir.",
                'Faible': "Vous pourriez préférer des métiers techniques, de recherche ou de création en autonomie."
            },
            'O': {
                'Élevé': "Les domaines créatifs, artistiques ou de recherche correspondent à votre profil.",
                'Faible': "Vous pourriez exceller dans des domaines nécessitant rigueur et méthode traditionnelle."
            },
            'A': {
                'Élevé': "Les métiers d'aide, d'enseignement ou de collaboration d'équipe vous conviendront.",
                'Faible': "Vous pourriez réussir dans des postes de négociation ou de leadership compétitif."
            },
            'C': {
                'Élevé': "Les métiers nécessitant organisation et persévérance correspondent à vos forces.",
                'Faible': "Privilégiez des environnements flexibles permettant la créativité et l'adaptation."
            }
        }

        st.markdown("#### 💼 Orientation Professionnelle")
        career_card = ""
        for dim, interp in st.session_state.interpretations.items():
            if interp['level'] in ['Élevé', 'Faible']:
                dim_name = neo_manager.dimensions[dim]
                recommendation = career_recommendations[dim].get(interp['level'], "")
                if recommendation:
                    career_card += f"• **{dim_name}** : {recommendation}\n"

        if career_card:
            st.markdown(f"""
            <div class="info-card">
                <h5 style="color: #2c3e50; margin-top: 0;">🎯 Suggestions d'orientation</h5>
                <div style="color: #34495e; line-height: 1.6;">
                    {career_card}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Relations interpersonnelles
        st.markdown("#### 👥 Relations Interpersonnelles")

        relationship_tips = []

        if st.session_state.interpretations['E']['level'] == 'Élevé':
            relationship_tips.append("Votre nature sociable est un atout. Veillez à laisser de l'espace aux personnes plus introverties.")
        elif st.session_state.interpretations['E']['level'] == 'Faible':
            relationship_tips.append("Votre préférence pour l'intimité est précieuse. N'hésitez pas à communiquer vos besoins d'espace.")

        if st.session_state.interpretations['A']['level'] == 'Élevé':
            relationship_tips.append("Votre bienveillance naturelle est appréciée. Attention à ne pas vous oublier.")
        elif st.session_state.interpretations['A']['level'] == 'Faible':
            relationship_tips.append("Votre franc-parler peut être rafraîchissant. Travaillez sur l'empathie pour renforcer vos relations.")

        if st.session_state.interpretations['N']['level'] == 'Élevé':
            relationship_tips.append("Votre sensibilité émotionnelle peut enrichir vos relations. Partagez vos besoins avec vos proches.")

        for tip in relationship_tips:
            st.markdown(f"""
            <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 10px 0;
                       border-left: 4px solid #3498db;">
                <p style="color: #2c3e50; margin: 0; line-height: 1.5;">
                    💭 {tip}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Développement personnel
        st.markdown("#### 🌱 Développement Personnel")

        development_suggestions = []

        for dim, interp in st.session_state.interpretations.items():
            dim_name = neo_manager.dimensions[dim]

            if dim == 'N' and interp['level'] == 'Élevé':
                development_suggestions.append("Pratiquez la méditation ou la relaxation pour gérer le stress")
            elif dim == 'E' and interp['level'] == 'Faible':
                development_suggestions.append("Fixez-vous des objectifs sociaux progressifs pour élargir votre réseau")
            elif dim == 'O' and interp['level'] == 'Faible':
                development_suggestions.append("Essayez une nouvelle activité créative ou culturelle chaque mois")
            elif dim == 'A' and interp['level'] == 'Faible':
                development_suggestions.append("Pratiquez l'écoute active et l'empathie dans vos interactions")
            elif dim == 'C' and interp['level'] == 'Faible':
                development_suggestions.append("Utilisez des outils d'organisation pour structurer vos projets")

        if development_suggestions:
            for suggestion in development_suggestions:
                st.markdown(f"""
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;
                           border-left: 4px solid #4169e1;">
                    <p style="color: #1e3a8a; margin: 0; line-height: 1.5;">
                        🚀 {suggestion}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        # Bouton pour refaire le test
        st.markdown("<br><br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Refaire le Test", use_container_width=True):
                # Reset de l'état
                st.session_state.test_started = False
                st.session_state.test_completed = False
                st.session_state.responses = {}
                st.session_state.current_question = 0
                st.session_state.scores = {}
                st.session_state.interpretations = {}
                st.session_state.tool_choice = "📝 Passer le Test"
                st.rerun()

def show_about_page():
    """Page à propos du test NEO PI-R"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #9b59b6, #8e44ad);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            ℹ️ À Propos du NEO PI-R
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Tout ce que vous devez savoir sur ce test de personnalité
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Histoire et développement
    st.markdown("""
    <div class="info-card">
        <h2 style="color: #3498db; margin-bottom: 25px; font-size: 2.2rem;">
            📚 Histoire et Développement
        </h2>
        <p style="font-size: 1.1rem; line-height: 1.8; color: #2c3e50; margin-bottom: 20px;">
            Le NEO PI-R a été développé par <strong>Paul T. Costa Jr.</strong> et <strong>Robert R. McCrae</strong>
            au National Institute on Aging (NIH) dans les années 1980-1990. Il s'agit de l'une des mesures
            les plus utilisées et validées scientifiquement pour évaluer la personnalité selon le modèle
            des Big Five.
        </p>
        <p style="font-size: 1.1rem; line-height: 1.8; color: #2c3e50;">
            Ce modèle est le fruit de décennies de recherche en psychologie de la personnalité et
            représente un consensus scientifique sur les dimensions fondamentales de la personnalité humaine.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Validité scientifique
    st.markdown("## 🔬 Validité Scientifique")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #e8f4fd; padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h4 style="color: #2980b9; margin-top: 0;">📊 Recherche Extensive</h4>
            <ul style="color: #34495e; padding-left: 20px; line-height: 1.6;">
                <li>Plus de 2000 études publiées</li>
                <li>Validé dans plus de 50 cultures</li>
                <li>Traduit en plus de 40 langues</li>
                <li>Utilisé dans la recherche depuis 30+ ans</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #fff3cd; padding: 20px; border-radius: 15px;">
            <h4 style="color: #856404; margin-top: 0;">🎯 Applications Cliniques</h4>
            <ul style="color: #856404; padding-left: 20px; line-height: 1.6;">
                <li>Orientation professionnelle</li>
                <li>Thérapie personnalisée</li>
                <li>Recherche en psychologie</li>
                <li>Développement personnel</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #d4edda; padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h4 style="color: #155724; margin-top: 0;">✅ Fiabilité Éprouvée</h4>
            <ul style="color: #155724; padding-left: 20px; line-height: 1.6;">
                <li>Consistance interne élevée (α > 0.85)</li>
                <li>Stabilité temporelle démontrée</li>
                <li>Validité convergente et discriminante</li>
                <li>Corrélations inter-évaluateurs fortes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #f8d7da; padding: 20px; border-radius: 15px;">
            <h4 style="color: #721c24; margin-top: 0;">🌍 Impact International</h4>
            <ul style="color: #721c24; padding-left: 20px; line-height: 1.6;">
                <li>Standard mondial en personnalité</li>
                <li>Référence pour autres tests</li>
                <li>Utilisé par l'OMS</li>
                <li>Intégré dans DSM et CIM</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Interprétation des scores
    st.markdown("## 📈 Comprendre Vos Scores")

    st.markdown("""
    <div class="info-card">
        <h4 style="color: #2c3e50; margin-top: 0;">📊 Système de Percentiles</h4>
        <p style="color: #34495e; line-height: 1.6; margin-bottom: 20px;">
            Vos scores sont exprimés en <strong>percentiles</strong>, ce qui signifie le pourcentage
            de personnes dans la population générale qui obtiennent un score inférieur au vôtre.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px; margin-top: 20px;">
            <div style="background: #3498db; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                <h5 style="margin: 0 0 10px 0;">0-30e percentile</h5>
                <p style="margin: 0; font-size: 0.9rem;">Score Faible</p>
            </div>
            <div style="background: #f39c12; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                <h5 style="margin: 0 0 10px 0;">30-70e percentile</h5>
                <p style="margin: 0; font-size: 0.9rem;">Score Moyen</p>
            </div>
            <div style="background: #e74c3c; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                <h5 style="margin: 0 0 10px 0;">70-100e percentile</h5>
                <p style="margin: 0; font-size: 0.9rem;">Score Élevé</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Limitations et considérations
    st.markdown("## ⚠️ Limitations et Considérations")

    st.markdown("""
    <div style="background: #fff3cd; padding: 20px; border-radius: 15px; margin: 20px 0;
               border-left: 4px solid #ffc107;">
        <h4 style="color: #856404; margin-top: 0;">🔍 Points Importants à Retenir</h4>
        <ul style="color: #856404; padding-left: 25px; line-height: 1.8;">
            <li><strong>Outil descriptif</strong> : Le test décrit votre personnalité, il ne la juge pas</li>
            <li><strong>Pas de profil parfait</strong> : Chaque combinaison de traits a ses avantages</li>
            <li><strong>Évolution possible</strong> : La personnalité peut changer avec l'âge et les expériences</li>
            <li><strong>Contexte culturel</strong> : Les normes peuvent varier selon les cultures</li>
            <li><strong>Complément d'information</strong> : À utiliser avec d'autres sources d'information</li>
            <li><strong>But éducatif</strong> : Ne remplace pas une évaluation psychologique professionnelle</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Utilisations recommandées
    st.markdown("## 🎯 Utilisations Recommandées")

    col1, col2, col3 = st.columns(3)

    uses = [
        {
            "title": "💭 Développement Personnel",
            "items": ["Mieux se comprendre", "Identifier ses forces", "Planifier sa croissance", "Améliorer ses relations"],
            "color": "#3498db"
        },
        {
            "title": "💼 Orientation Professionnelle",
            "items": ["Choix de carrière", "Style de management", "Dynamique d'équipe", "Formation continue"],
            "color": "#2ecc71"
        },
        {
            "title": "🎓 Contexte Éducatif",
            "items": ["Orientation scolaire", "Méthodes d'apprentissage", "Projets de groupe", "Développement étudiant"],
            "color": "#9b59b6"
        }
    ]

    for i, (use, col) in enumerate(zip(uses, [col1, col2, col3])):
        with col:
            items_html = "".join([f"<li>{item}</li>" for item in use['items']])
            st.markdown(f"""
            <div style="background: {use['color']}; color: white;
                       padding: 25px; border-radius: 15px; height: 280px;">
                <h4 style="margin: 0 0 20px 0; font-size: 1.2rem;
                          border-bottom: 2px solid rgba(255,255,255,0.3); padding-bottom: 10px;">
                    {use['title']}
                </h4>
                <ul style="padding-left: 20px; margin: 0; line-height: 1.6;">
                    {items_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # Ressources supplémentaires
    st.markdown("## 📚 Ressources Supplémentaires")

    st.markdown("""
    <div class="info-card">
        <h4 style="color: #2c3e50; margin-top: 0;">📖 Pour Aller Plus Loin</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px; margin-top: 20px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h5 style="color: #3498db; margin: 0 0 10px 0;">📚 Livres Recommandés</h5>
                <ul style="color: #6c757d; font-size: 0.9rem; padding-left: 20px;">
                    <li>"Personality in Adulthood" - Costa & McCrae</li>
                    <li>"The Big Five Personality Dimensions" - Goldberg</li>
                    <li>"Personality Psychology" - Larsen & Buss</li>
                </ul>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h5 style="color: #3498db; margin: 0 0 10px 0;">🔗 Sites Web Utiles</h5>
                <ul style="color: #6c757d; font-size: 0.9rem; padding-left: 20px;">
                    <li>American Psychological Association</li>
                    <li>International Personality Psychology</li>
                    <li>Research Gate Publications</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Contact et support
    st.markdown("## 📞 Contact et Support")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2);
               color: white; padding: 30px; border-radius: 15px; text-align: center;">
        <h4 style="margin: 0 0 20px 0; font-size: 1.5rem;">💬 Besoin d'Aide ?</h4>
        <p style="margin: 0 0 15px 0; line-height: 1.6;">
            Si vous avez des questions sur vos résultats ou souhaitez approfondir votre analyse,
            n'hésitez pas à consulter un professionnel de la psychologie.
        </p>
        <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">
            Ce test est fourni à des fins éducatives et de développement personnel uniquement.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ================= FONCTION PRINCIPALE =================

def main():
    """Fonction principale de l'application"""
    # Initialisation
    initialize_session_state()
    set_custom_theme()

    # Initialisation du gestionnaire de sécurité
    if 'security_manager' not in st.session_state:
        st.session_state.security_manager = SecurityManager()

    # Sidebar avec navigation
    with st.sidebar:
        tool_choice = show_navigation_menu()

    # Routage des pages
    if tool_choice == "🏠 Accueil":
        show_home_page()
    elif tool_choice == "📝 Passer le Test":
        show_test_page()
    elif tool_choice == "📊 Résultats":
        show_results_page()
    elif tool_choice == "ℹ️ À propos":
        show_about_page()

# ================= POINT D'ENTRÉE =================

if __name__ == "__main__":
    main()
