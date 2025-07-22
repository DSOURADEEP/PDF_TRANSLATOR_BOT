#!/usr/bin/env python3
"""
PDF Translation Bot - Command Line Interface
Interactive CLI for translating PDF documents
"""

import argparse
import sys
import os
from pathlib import Path
from colorama import init, Fore, Style
from pdf_translator import PDFTranslator

# Initialize colorama for Windows compatibility
init(autoreset=True)


def print_banner():
    """Print a colorful banner"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                  📄 PDF TRANSLATION BOT 📄                   ║
║                                                              ║
║         Translate PDFs from any language to English         ║
║            With batch processing capabilities!               ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def print_supported_languages(translator):
    """Print supported languages in a nice format"""
    print(f"\n{Fore.YELLOW}🌍 SUPPORTED LANGUAGES:{Style.RESET_ALL}")
    languages = translator.get_supported_languages()
    
    # Group languages in columns for better display
    lang_items = list(languages.items())
    cols = 3
    for i in range(0, len(lang_items), cols):
        row = lang_items[i:i+cols]
        line = ""
        for name, code in row:
            line += f"{Fore.GREEN}{name.title():<12}{Style.RESET_ALL}({code})  "
        print(f"  {line}")
    print()


def interactive_mode():
    """Run interactive mode"""
    print_banner()
    
    translator = PDFTranslator(output_dir="translated_pdfs")
    print_supported_languages(translator)
    
    while True:
        print(f"\n{Fore.CYAN}=== MAIN MENU ==={Style.RESET_ALL}")
        print("1. 📄 Translate single PDF")
        print("2. 📁 Batch translate PDFs")
        print("3. 🌍 View supported languages")
        print("4. ❌ Exit")
        
        choice = input(f"\n{Fore.YELLOW}Enter your choice (1-4): {Style.RESET_ALL}").strip()
        
        if choice == '1':
            single_pdf_mode(translator)
        elif choice == '2':
            batch_mode(translator)
        elif choice == '3':
            print_supported_languages(translator)
        elif choice == '4':
            print(f"\n{Fore.GREEN}👋 Thank you for using PDF Translation Bot!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")


def single_pdf_mode(translator):
    """Handle single PDF translation"""
    print(f"\n{Fore.CYAN}=== SINGLE PDF TRANSLATION ==={Style.RESET_ALL}")
    
    # Get input file
    while True:
        pdf_path = input(f"{Fore.YELLOW}Enter path to PDF file: {Style.RESET_ALL}").strip().strip('"')
        if os.path.exists(pdf_path):
            break
        print(f"{Fore.RED}❌ File not found. Please try again.{Style.RESET_ALL}")
    
    # Get source language
    print(f"\n{Fore.CYAN}Language Detection:{Style.RESET_ALL}")
    print("1. Auto-detect language")
    print("2. Specify language manually")
    
    lang_choice = input(f"{Fore.YELLOW}Choose option (1-2): {Style.RESET_ALL}").strip()
    
    source_lang = 'auto'
    if lang_choice == '2':
        print_supported_languages(translator)
        lang_input = input(f"{Fore.YELLOW}Enter language code or name: {Style.RESET_ALL}").strip().lower()
        
        # Check if it's a language name or code
        languages = translator.get_supported_languages()
        if lang_input in languages.values():
            source_lang = lang_input
        elif lang_input in languages:
            source_lang = languages[lang_input]
        else:
            print(f"{Fore.YELLOW}⚠️  Language not found. Using auto-detection.{Style.RESET_ALL}")
    
    # Custom output filename
    custom_name = input(f"{Fore.YELLOW}Custom output filename (press Enter for default): {Style.RESET_ALL}").strip()
    output_filename = custom_name if custom_name else None
    
    # Perform translation
    try:
        print(f"\n{Fore.GREEN}🚀 Starting translation...{Style.RESET_ALL}")
        output_path = translator.translate_single_pdf(pdf_path, output_filename, source_lang)
        print(f"\n{Fore.GREEN}✅ Translation completed successfully!{Style.RESET_ALL}")
        print(f"📄 Translated PDF saved to: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Translation failed: {str(e)}{Style.RESET_ALL}")


def batch_mode(translator):
    """Handle batch PDF translation"""
    print(f"\n{Fore.CYAN}=== BATCH PDF TRANSLATION ==={Style.RESET_ALL}")
    
    # Get input directory
    while True:
        dir_path = input(f"{Fore.YELLOW}Enter directory path containing PDFs: {Style.RESET_ALL}").strip().strip('"')
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            break
        print(f"{Fore.RED}❌ Directory not found. Please try again.{Style.RESET_ALL}")
    
    # File pattern
    pattern = input(f"{Fore.YELLOW}File pattern (default: *.pdf): {Style.RESET_ALL}").strip()
    if not pattern:
        pattern = "*.pdf"
    
    # Get source language
    print(f"\n{Fore.CYAN}Language Detection:{Style.RESET_ALL}")
    print("1. Auto-detect language for each file")
    print("2. Use same language for all files")
    
    lang_choice = input(f"{Fore.YELLOW}Choose option (1-2): {Style.RESET_ALL}").strip()
    
    source_lang = 'auto'
    if lang_choice == '2':
        print_supported_languages(translator)
        lang_input = input(f"{Fore.YELLOW}Enter language code or name: {Style.RESET_ALL}").strip().lower()
        
        # Check if it's a language name or code
        languages = translator.get_supported_languages()
        if lang_input in languages.values():
            source_lang = lang_input
        elif lang_input in languages:
            source_lang = languages[lang_input]
        else:
            print(f"{Fore.YELLOW}⚠️  Language not found. Using auto-detection.{Style.RESET_ALL}")
    
    # Perform batch translation
    try:
        print(f"\n{Fore.GREEN}🚀 Starting batch translation...{Style.RESET_ALL}")
        translated_files = translator.batch_translate_pdfs(dir_path, pattern, source_lang)
        
        print(f"\n{Fore.GREEN}✅ Batch translation completed!{Style.RESET_ALL}")
        print(f"📊 Successfully translated: {Fore.CYAN}{len(translated_files)}{Style.RESET_ALL} files")
        
        if translated_files:
            print(f"\n{Fore.CYAN}📄 Translated files:{Style.RESET_ALL}")
            for file_path in translated_files:
                print(f"  • {file_path}")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Batch translation failed: {str(e)}{Style.RESET_ALL}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="PDF Translation Bot - Translate PDFs to English",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                           # Interactive mode
  python cli.py -f document.pdf           # Translate single PDF
  python cli.py -d ./pdfs --batch         # Batch translate directory
  python cli.py -f doc.pdf -l spanish     # Translate with specific source language
  python cli.py -d ./pdfs --batch -o ./translated  # Custom output directory
        """
    )
    
    parser.add_argument('-f', '--file', help='PDF file to translate')
    parser.add_argument('-d', '--directory', help='Directory containing PDFs for batch processing')
    parser.add_argument('--batch', action='store_true', help='Enable batch processing mode')
    parser.add_argument('-l', '--language', default='auto', help='Source language (default: auto-detect)')
    parser.add_argument('-o', '--output', default='translated_pdfs', help='Output directory (default: translated_pdfs)')
    parser.add_argument('--pattern', default='*.pdf', help='File pattern for batch processing (default: *.pdf)')
    parser.add_argument('-n', '--name', help='Custom output filename for single file translation')
    parser.add_argument('--list-languages', action='store_true', help='List supported languages and exit')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up translator
    log_level = 'DEBUG' if args.verbose else 'INFO'
    translator = PDFTranslator(output_dir=args.output, log_level=log_level)
    
    # Handle list languages
    if args.list_languages:
        print_banner()
        print_supported_languages(translator)
        return
    
    # Handle command line arguments
    if args.file:
        # Single file translation
        try:
            print_banner()
            print(f"{Fore.GREEN}🚀 Translating: {args.file}{Style.RESET_ALL}")
            
            # Validate language
            source_lang = args.language
            if source_lang != 'auto':
                languages = translator.get_supported_languages()
                if source_lang not in languages.values() and source_lang not in languages:
                    lang_code = languages.get(source_lang.lower())
                    source_lang = lang_code if lang_code else 'auto'
                    if source_lang == 'auto':
                        print(f"{Fore.YELLOW}⚠️  Language '{args.language}' not found. Using auto-detection.{Style.RESET_ALL}")
            
            output_path = translator.translate_single_pdf(args.file, args.name, source_lang)
            print(f"\n{Fore.GREEN}✅ Translation completed!{Style.RESET_ALL}")
            print(f"📄 Saved to: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Translation failed: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
    
    elif args.batch and args.directory:
        # Batch translation
        try:
            print_banner()
            print(f"{Fore.GREEN}🚀 Batch translating PDFs in: {args.directory}{Style.RESET_ALL}")
            
            # Validate language
            source_lang = args.language
            if source_lang != 'auto':
                languages = translator.get_supported_languages()
                if source_lang not in languages.values() and source_lang not in languages:
                    lang_code = languages.get(source_lang.lower())
                    source_lang = lang_code if lang_code else 'auto'
                    if source_lang == 'auto':
                        print(f"{Fore.YELLOW}⚠️  Language '{args.language}' not found. Using auto-detection.{Style.RESET_ALL}")
            
            translated_files = translator.batch_translate_pdfs(args.directory, args.pattern, source_lang)
            print(f"\n{Fore.GREEN}✅ Batch translation completed!{Style.RESET_ALL}")
            print(f"📊 Successfully translated: {Fore.CYAN}{len(translated_files)}{Style.RESET_ALL} files")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Batch translation failed: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
    
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
