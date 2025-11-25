"""
Text cleaning utilities for removing HTML tags and special characters
"""
import html
import re
from bs4 import BeautifulSoup


def clean_html_to_text(text: str, keep_emojis: bool = False) -> str:
    """
    Converts HTML/Markdown to clean plain text
    
    Args:
        text: Text with HTML or markdown
        keep_emojis: If True, keeps emojis; if False, removes them
    
    Returns:
        Clean text without HTML tags or special characters
    
    Example:
        >>> clean_html_to_text("<p>Hello <strong>World</strong></p>")
        "Hello World"
        
        >>> clean_html_to_text("<p>C &amp; C++</p>")
        "C & C++"
    """
    if not text:
        return ""
    
    # 1. Remove HTML tags if they exist
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator='\n')
    
    # 2. Decode HTML entities (&amp; → &, &lt; → <, etc.)
    clean_text = html.unescape(clean_text)
    
    # 3. Remove emojis if requested
    if not keep_emojis:
        # Regex to remove Unicode emojis
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U00002600-\U000026FF"  # misc symbols
            "]+", flags=re.UNICODE
        )
        clean_text = emoji_pattern.sub('', clean_text)
    
    # 4. Clean up excessive whitespace
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)  # Max 2 line breaks
    clean_text = re.sub(r' +', ' ', clean_text)  # Remove multiple spaces
    clean_text = clean_text.strip()
    
    return clean_text


def remove_markdown_formatting(text: str) -> str:
    """
    Removes markdown formatting like **bold**, _italic_, [links](url)
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Plain text without markdown syntax
    """
    if not text:
        return ""
    
    # Remove bold/italic: **text** or __text__
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # Remove italic: *text* or _text_
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove inline code: `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    return text.strip()
