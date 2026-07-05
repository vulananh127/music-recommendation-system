import asyncpg
import os

async def get_pool():
    return await asyncpg.create_pool(
        host=os.environ.get("DB_HOST", "postgres"),
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ.get("DB_USER", "reco_user"),
        password=os.environ.get("DB_PASSWORD", "reco_pass"),
        database=os.environ.get("DB_NAME", "reco_db"),
        
        # Connection Pool Settings
        min_size=5,              
        max_size=50,             
        
        # Timeout Settings
        command_timeout=60,      
        timeout=30,              
        
        # Connection Lifecycle
        max_queries=50000,       
        max_inactive_connection_lifetime=300,  
        
        # Performance Settings
        server_settings={
            'jit': 'off',        
            'application_name': 'music_recommendation_api'
        }
    )