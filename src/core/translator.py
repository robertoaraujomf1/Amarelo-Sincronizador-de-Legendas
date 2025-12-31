import requests
import time
import random
# Alterado para PyQt6
from PyQt6.QtCore import QObject, pyqtSignal

class Translator(QObject):
    """Componente de Tradução (Google / DeepL)"""
    
    # Sinal para atualizar a barra de progresso específica da tradução
    progress_signal = pyqtSignal(float)
    
    def __init__(self, service='google'):
        super().__init__()
        self.service = service
        self.session = requests.Session()
        # User-agent para evitar bloqueios simples do Google
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def translate_batch(self, subtitles, target_language, source_language='auto'):
        """Traduz uma lista de dicionários de legenda"""
        translated_list = []
        total = len(subtitles)
        
        # O código de idioma do Google para PT-BR é 'pt'
        target_lang_code = target_language.split('-')[0]
        
        for i, subtitle in enumerate(subtitles):
            try:
                original_text = subtitle.get('text', '')
                
                # Tradução do texto
                translated_text = self.translate_text(
                    original_text, 
                    target_lang_code, 
                    source_language
                )
                
                # Monta o novo objeto preservando tempos
                entry = {
                    'start': subtitle['start'],
                    'end': subtitle['end'],
                    'original_text': original_text,
                    'text': translated_text
                }
                
                translated_list.append(entry)
                
                # Emite progresso (0 a 100)
                progress = ((i + 1) / total) * 100
                self.progress_signal.emit(progress)
                
                # Delay randômico para simular comportamento humano e evitar IP Ban
                if self.service == 'google':
                    time.sleep(random.uniform(0.2, 0.5))
                
            except Exception as e:
                # Fallback: Se falhar, mantém o original para não quebrar o fluxo
                translated_list.append({
                    'start': subtitle['start'],
                    'end': subtitle['end'],
                    'original_text': subtitle.get('text', ''),
                    'text': f"[Erro] {subtitle.get('text', '')}"
                })
                
        return translated_list
        
    def translate_text(self, text, target_language, source_language='auto'):
        """Seleciona o serviço de tradução"""
        if not text or not text.strip():
            return text
            
        if self.service == 'deepl':
            return self._translate_deepl(text, target_language, source_language)
        
        # Padrão: Google
        return self._translate_google(text, target_language, source_language)

    def _translate_google(self, text, target_lang, source_lang):
        """Implementação robusta usando a API de tradução do Google (Client gtx)"""
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': source_lang,
            'tl': target_lang,
            'dt': 't',
            'q': text
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            # O Google retorna uma lista aninhada onde result[0] contém as partes do texto
            if result and result[0]:
                full_translation = "".join([part[0] for part in result[0] if part[0]])
                return full_translation
            return text
        except Exception:
            return f"Error: {text}"

    def _translate_deepl(self, text, target_lang, source_lang):
        """Implementação para DeepL API (Requer chave de API)"""
        # Exemplo de URL para API gratuita
        url = "https://api-free.deepl.com/v2/translate"
        
        # Nota: Idealmente, carregar do seu ConfigManager
        api_key = "SUA_CHAVE_AQUI" 
        
        if api_key == "SUA_CHAVE_AQUI":
            return self._translate_google(text, target_lang, source_lang)

        data = {
            'auth_key': api_key,
            'text': text,
            'target_lang': target_lang.upper(),
            'source_lang': source_lang.upper() if source_lang != 'auto' else None
        }
        
        try:
            res = self.session.post(url, data=data, timeout=10)
            return res.json()['translations'][0]['text']
        except:
            return self._translate_google(text, target_lang, source_lang)