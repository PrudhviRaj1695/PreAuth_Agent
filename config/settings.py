import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class ProductionConfig:
    """Production configuration with Azure integration"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.debug = False
        
        # Azure Key Vault setup
        self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        if self.key_vault_url:
            credential = DefaultAzureCredential()
            self.secret_client = SecretClient(vault_url=self.key_vault_url, credential=credential)
        else:
            self.secret_client = None
    
    def get_secret(self, secret_name: str, default: str = None) -> str:
        """Get secret from Azure Key Vault or environment"""
        try:
            if self.secret_client:
                secret = self.secret_client.get_secret(secret_name)
                return secret.value
        except Exception:
            pass
        return os.getenv(secret_name, default)
    
    @property
    def database_url(self) -> str:
        return self.get_secret('DATABASE_URL', 'sqlite:///./data/patients.db')
    
    @property
    def azure_storage_connection_string(self) -> str:
        return self.get_secret('AZURE_STORAGE_CONNECTION_STRING')

config = ProductionConfig()
