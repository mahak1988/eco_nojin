"""
Supabase client for Eco Nojin.

Usage:
    from services.supabase.client import get_supabase_client
    
    client = get_supabase_client()
    data = client.table('platform_landscapes').select('*').execute()
"""
import os
from typing import Optional
from pathlib import Path

# Load .env file automatically
try:
    from dotenv import load_dotenv
    
    # Find .env in project root
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try current directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, use system env vars
    pass

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError(
        "supabase is required. Install with: pip install supabase python-dotenv"
    )


_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url:
            raise ValueError(
                "SUPABASE_URL not set. Check your .env file or environment variables."
            )
        if not key:
            raise ValueError(
                "SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY not set. Check your .env file."
            )
        
        _client = create_client(url, key)
    
    return _client


def get_anon_client() -> Client:
    """Get Supabase client with anon key (for client-side operations)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    
    return create_client(url, key)