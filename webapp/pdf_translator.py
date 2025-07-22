import PyPDF2
from googletrans import Translator
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
import os
import time
from pathlib import Path
from tqdm import tqdm
import logging
from typing import List, Optional, Dict, Tuple
import re
import unicodedata


class PDFTranslator:
    """
    A comprehensive PDF translator that extracts text from PDFs,
    translates it to English, and creates new translated PDFs.
    """
    
    SUPPORTED_LANGUAGES = {
        'finnish': 'fi',
        'french': 'fr', 
        'spanish': 'es',
        'german': 'de',
        'italian': 'it',
        'portuguese': 'pt',
        'russian': 'ru',
        'chinese': 'zh',
        'japanese': 'ja',
        'korean': 'ko',
        'dutch': 'nl',
        'swedish': 'sv',
        'norwegian': 'no',
        'danish': 'da',
        'polish': 'pl'
    }
    
    def __init__(self, output_dir: str = "translated_pdfs", log_level: str = "INFO"):
        """
        Initialize the PDF Translator
        
        Args:
            output_dir: Directory to save translated PDFs
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.translator = Translator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdf_translator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Translation settings
        self.chunk_size = 3000  # Characters per translation chunk (smaller for better quality)
        self.delay_between_requests = 0.2  # Seconds (slower for better quality)
        
        # Simplified preservation patterns - only the most critical items
        self.preserve_patterns = [
            # Personal names (most important)
            r'\b[A-Z][a-z]{2,} [A-Z][a-z]{2,}\b',  # First Last (min 3 chars each)
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Company names with specific suffixes
            r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:Inc|Ltd|LLC|Corp|Company|University|College)\b',
        ]
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                self.logger.info(f"Extracted {len(text)} characters from {pdf_path}")
                return text.strip()
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> Dict[str, str]:
        """
        Detect the language of the input text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language code and confidence
        """
        try:
            # Use first 1000 characters for language detection
            sample = text[:1000] if len(text) > 1000 else text
            detection = self.translator.detect(sample)
            
            lang_name = [k for k, v in self.SUPPORTED_LANGUAGES.items() if v == detection.lang]
            lang_name = lang_name[0] if lang_name else detection.lang
            
            self.logger.info(f"Detected language: {lang_name} ({detection.lang}) with confidence {detection.confidence}")
            
            return {
                'language': detection.lang,
                'language_name': lang_name,
                'confidence': detection.confidence
            }
        except Exception as e:
            self.logger.warning(f"Language detection failed: {str(e)}")
            return {'language': 'unknown', 'language_name': 'unknown', 'confidence': 0.0}
    
    def preserve_proper_nouns(self, text: str) -> Tuple[str, dict]:
        """
        Replace proper nouns with placeholders to preserve them during translation
        
        Args:
            text: Original text
            
        Returns:
            Tuple of (text_with_placeholders, preservation_map)
        """
        preservation_map = {}
        protected_text = text
        placeholder_counter = 0
        all_matches = []
        
        # Collect all matches first to avoid overlapping replacements
        for pattern in self.preserve_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Check if this match overlaps with existing matches
                overlap = False
                for existing_match in all_matches:
                    if (match.start() < existing_match['end'] and match.end() > existing_match['start']):
                        overlap = True
                        break
                
                if not overlap:
                    all_matches.append({
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end()
                    })
        
        # Sort matches by start position in reverse order (from end to start)
        # This prevents position shifts during replacement
        all_matches.sort(key=lambda x: x['start'], reverse=True)
        
        # Replace matches with placeholders using invisible Unicode characters
        for match in all_matches:
            original_text = match['text']
            # Use invisible Unicode characters as separators
            placeholder = f"\u200b{placeholder_counter}\u200c{original_text}\u200d"
            preservation_map[placeholder] = original_text
            
            # Replace using position to ensure exact match
            protected_text = (protected_text[:match['start']] + 
                            placeholder + 
                            protected_text[match['end']:])
            placeholder_counter += 1
        
        self.logger.info(f"Preserved {len(preservation_map)} proper nouns/entities")
        if preservation_map:
            self.logger.debug(f"Preserved entities: {list(preservation_map.values())}")
        
        return protected_text, preservation_map
    
    def restore_proper_nouns(self, translated_text: str, preservation_map: dict) -> str:
        """
        Restore preserved proper nouns from placeholders
        
        Args:
            translated_text: Text with placeholders
            preservation_map: Map of placeholders to original text
            
        Returns:
            Text with proper nouns restored
        """
        restored_text = translated_text
        restored_count = 0
        
        # First try exact matches
        for placeholder, original_text in preservation_map.items():
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original_text)
                restored_count += 1
        
        # Then try to find partial matches where Unicode characters might be removed
        for placeholder, original_text in preservation_map.items():
            # Extract the number and original text from Unicode placeholder: \u200b{number}\u200c{text}\u200d
            match = re.search(r'\u200b(\d+)\u200c(.+?)\u200d', placeholder)
            if match:
                number = match.group(1)
                expected_text = match.group(2)
                
                # Look for patterns where Unicode chars are stripped but number and text remain
                # This handles cases where Google Translate removes Unicode characters
                patterns_to_try = [
                    f"{number}{expected_text}",  # Number + text directly
                    f"{number} {expected_text}",  # Number + space + text
                    expected_text,  # Just the original text
                ]
                
                for pattern in patterns_to_try:
                    if pattern in restored_text and pattern != original_text:
                        restored_text = restored_text.replace(pattern, original_text)
                        restored_count += 1
                        break
        
        self.logger.info(f"Restored {restored_count} proper nouns/entities")
        if restored_count != len(preservation_map):
            self.logger.warning(f"Could not restore {len(preservation_map) - restored_count} placeholders")
            
        return restored_text
    
    def translate_text_chunks(self, text: str, source_lang: str = 'auto', target_lang: str = 'en') -> str:
        """
        Translate text in chunks to handle API limits
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if not text.strip():
            return text
            
        # Split text into chunks
        chunks = [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]
        translated_chunks = []
        
        self.logger.info(f"Translating {len(chunks)} chunks from {source_lang} to {target_lang}")
        
        for i, chunk in enumerate(tqdm(chunks, desc="Translating chunks")):
            try:
                # Add delay to respect API limits
                if i > 0:
                    time.sleep(self.delay_between_requests)
                
                translated = self.translator.translate(chunk, src=source_lang, dest=target_lang)
                translated_chunks.append(translated.text)
                
            except Exception as e:
                self.logger.warning(f"Failed to translate chunk {i}: {str(e)}")
                # Add original text if translation fails
                translated_chunks.append(chunk)
                
        return ' '.join(translated_chunks)
    
    def create_pdf_from_text(self, text: str, output_path: str, title: str = "Translated Document") -> None:
        """
        Create a new PDF from translated text
        
        Args:
            text: Translated text content
            output_path: Path for the new PDF
            title: Title for the document
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_LEFT
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                leftIndent=0,
                rightIndent=0
            )
            
            # Build document content
            story = []
            
            # Add title
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Split text into paragraphs and add them
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Clean up the text for PDF
                    clean_para = para.strip().replace('\n', ' ')
                    story.append(Paragraph(clean_para, body_style))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            self.logger.info(f"Created translated PDF: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating PDF {output_path}: {str(e)}")
            raise
    
    def translate_single_pdf(self, input_path: str, output_filename: Optional[str] = None, 
                           source_lang: str = 'auto') -> str:
        """
        Translate a single PDF file
        
        Args:
            input_path: Path to input PDF
            output_filename: Custom output filename (optional)
            source_lang: Source language code (auto-detect if 'auto')
            
        Returns:
            Path to translated PDF
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self.logger.info(f"Starting translation of: {input_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(str(input_path))
        
        if not text.strip():
            raise ValueError("No text found in PDF")
        
        # Detect language if auto
        if source_lang == 'auto':
            detection = self.detect_language(text)
            source_lang = detection['language']
            self.logger.info(f"Auto-detected language: {detection['language_name']}")
        
        # Translate text directly without preservation
        final_text = self.translate_text_chunks(text, source_lang, 'en')
        
        # Generate output filename
        if not output_filename:
            output_filename = f"{input_path.stem}_translated_en.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create translated PDF
        title = f"Translated: {input_path.name}"
        self.create_pdf_from_text(final_text, str(output_path), title)
        
        self.logger.info(f"Translation completed: {output_path}")
        return str(output_path)
    
    def batch_translate_pdfs(self, input_directory: str, pattern: str = "*.pdf", 
                           source_lang: str = 'auto') -> List[str]:
        """
        Batch translate multiple PDF files
        
        Args:
            input_directory: Directory containing PDF files
            pattern: File pattern to match (default: "*.pdf")
            source_lang: Source language code
            
        Returns:
            List of translated PDF paths
        """
        input_dir = Path(input_directory)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_directory}")
        
        # Find PDF files
        pdf_files = list(input_dir.glob(pattern))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {input_directory} with pattern {pattern}")
            return []
        
        self.logger.info(f"Found {len(pdf_files)} PDF files for batch translation")
        
        translated_files = []
        failed_files = []
        
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                output_path = self.translate_single_pdf(str(pdf_file), source_lang=source_lang)
                translated_files.append(output_path)
                
            except Exception as e:
                self.logger.error(f"Failed to translate {pdf_file}: {str(e)}")
                failed_files.append(str(pdf_file))
        
        # Summary
        self.logger.info(f"Batch translation completed:")
        self.logger.info(f"  Successfully translated: {len(translated_files)} files")
        self.logger.info(f"  Failed: {len(failed_files)} files")
        
        if failed_files:
            self.logger.warning(f"Failed files: {failed_files}")
        
        return translated_files
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()


if __name__ == "__main__":
    # Example usage
    translator = PDFTranslator(output_dir="translated_pdfs")
    
    # Display supported languages
    print("Supported Languages:")
    for lang_name, lang_code in translator.get_supported_languages().items():
        print(f"  {lang_name.title()}: {lang_code}")
    
    print("\nPDF Translator initialized. Use the CLI or import this module to start translating!")
