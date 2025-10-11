#!/usr/bin/env python3
"""
Arquitectura Cloud Híbrida para Aplicación de Banca Móvil
=========================================================

Este archivo contiene:
1. Diseño de arquitectura cloud híbrida con funciones serverless
2. Código backend básico para operaciones bancarias
3. Diagrama arquitectónico en formato Mermaid
4. Especificaciones de seguridad y escalabilidad

Autor: Fatima Gonzalez Romo
Fecha: 2024
"""

import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# =============================================================================
# 1. MODELOS DE DATOS Y ENUMERACIONES
# =============================================================================

class TransactionType(Enum):
    """Tipos de transacciones bancarias"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    LOAN_PAYMENT = "loan_payment"

class AccountType(Enum):
    """Tipos de cuenta bancaria"""
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    CREDIT = "credit"

class TransactionStatus(Enum):
    """Estados de transacciones"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class User:
    """Modelo de usuario"""
    user_id: str
    email: str
    phone: str
    full_name: str
    created_at: datetime
    is_verified: bool = False
    kyc_status: str = "pending"

@dataclass
class Account:
    """Modelo de cuenta bancaria"""
    account_id: str
    user_id: str
    account_number: str
    account_type: AccountType
    balance: float
    currency: str = "USD"
    created_at: datetime = None
    is_active: bool = True

@dataclass
class Transaction:
    """Modelo de transacción"""
    transaction_id: str
    from_account_id: str
    to_account_id: Optional[str]
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    description: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    reference_number: str = None

# =============================================================================
# 2. SERVICIOS SERVERLESS - FUNCIONES LAMBDA/AZURE FUNCTIONS
# =============================================================================

class AuthenticationService:
    """Servicio de autenticación serverless"""
    
    def __init__(self):
        self.secret_key = "banking_app_secret_key_2024"
    
    def generate_jwt_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """Genera token JWT para autenticación"""
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        payload = {
            "user_id": user_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + (expires_in_hours * 3600)
        }
        
        # Simulación de JWT (en producción usaría jwt library)
        token = f"{json.dumps(header)}.{json.dumps(payload)}.{self._sign_token(header, payload)}"
        return token
    
    def _sign_token(self, header: dict, payload: dict) -> str:
        """Firma el token con HMAC"""
        message = f"{json.dumps(header)}.{json.dumps(payload)}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verifica y extrae user_id del token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            payload = json.loads(parts[1])
            current_time = int(time.time())
            
            if payload.get('exp', 0) < current_time:
                return None
            
            return payload.get('user_id')
        except:
            return None

class AccountService:
    """Servicio de gestión de cuentas serverless"""
    
    def __init__(self):
        self.accounts_db = {}  # Simulación de base de datos
    
    def create_account(self, user_id: str, account_type: AccountType) -> Account:
        """Crea una nueva cuenta bancaria"""
        account_id = str(uuid.uuid4())
        account_number = self._generate_account_number()
        
        account = Account(
            account_id=account_id,
            user_id=user_id,
            account_number=account_number,
            account_type=account_type,
            balance=0.0,
            created_at=datetime.now()
        )
        
        self.accounts_db[account_id] = account
        return account
    
    def get_account_balance(self, account_id: str) -> Optional[float]:
        """Obtiene el saldo de una cuenta"""
        account = self.accounts_db.get(account_id)
        return account.balance if account else None
    
    def update_balance(self, account_id: str, amount: float) -> bool:
        """Actualiza el saldo de una cuenta"""
        account = self.accounts_db.get(account_id)
        if not account:
            return False
        
        new_balance = account.balance + amount
        if new_balance < 0:
            return False  # Saldo insuficiente
        
        account.balance = new_balance
        return True
    
    def _generate_account_number(self) -> str:
        """Genera número de cuenta único"""
        return f"ACC{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

class TransactionService:
    """Servicio de transacciones serverless"""
    
    def __init__(self):
        self.transactions_db = {}
        self.account_service = AccountService()
    
    def process_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Procesa una transacción bancaria"""
        result = {
            "success": False,
            "transaction_id": transaction.transaction_id,
            "message": "",
            "new_balance": None
        }
        
        try:
            # Validar transacción
            if not self._validate_transaction(transaction):
                result["message"] = "Transacción inválida"
                return result
            
            # Procesar según tipo
            if transaction.transaction_type == TransactionType.DEPOSIT:
                success = self.account_service.update_balance(
                    transaction.to_account_id, 
                    transaction.amount
                )
                if success:
                    transaction.status = TransactionStatus.COMPLETED
                    result["new_balance"] = self.account_service.get_account_balance(
                        transaction.to_account_id
                    )
                else:
                    transaction.status = TransactionStatus.FAILED
                    result["message"] = "Error al procesar depósito"
            
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                success = self.account_service.update_balance(
                    transaction.from_account_id, 
                    -transaction.amount
                )
                if success:
                    transaction.status = TransactionStatus.COMPLETED
                    result["new_balance"] = self.account_service.get_account_balance(
                        transaction.from_account_id
                    )
                else:
                    transaction.status = TransactionStatus.FAILED
                    result["message"] = "Saldo insuficiente"
            
            elif transaction.transaction_type == TransactionType.TRANSFER:
                # Retirar de cuenta origen
                withdraw_success = self.account_service.update_balance(
                    transaction.from_account_id, 
                    -transaction.amount
                )
                
                if withdraw_success:
                    # Depositar en cuenta destino
                    deposit_success = self.account_service.update_balance(
                        transaction.to_account_id, 
                        transaction.amount
                    )
                    
                    if deposit_success:
                        transaction.status = TransactionStatus.COMPLETED
                        result["new_balance"] = self.account_service.get_account_balance(
                            transaction.from_account_id
                        )
                    else:
                        # Revertir retiro si falla el depósito
                        self.account_service.update_balance(
                            transaction.from_account_id, 
                            transaction.amount
                        )
                        transaction.status = TransactionStatus.FAILED
                        result["message"] = "Error al procesar transferencia"
                else:
                    transaction.status = TransactionStatus.FAILED
                    result["message"] = "Saldo insuficiente para transferencia"
            
            transaction.processed_at = datetime.now()
            self.transactions_db[transaction.transaction_id] = transaction
            
            if transaction.status == TransactionStatus.COMPLETED:
                result["success"] = True
                result["message"] = "Transacción procesada exitosamente"
            
        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            result["message"] = f"Error interno: {str(e)}"
        
        return result
    
    def _validate_transaction(self, transaction: Transaction) -> bool:
        """Valida una transacción antes de procesarla"""
        if transaction.amount <= 0:
            return False
        
        if transaction.transaction_type in [TransactionType.DEPOSIT, TransactionType.TRANSFER]:
            if not transaction.to_account_id:
                return False
        
        if transaction.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER]:
            if not transaction.from_account_id:
                return False
        
        return True

class NotificationService:
    """Servicio de notificaciones serverless"""
    
    def send_transaction_notification(self, user_id: str, transaction: Transaction) -> bool:
        """Envía notificación de transacción"""
        message = self._format_transaction_message(transaction)
        
        # Simulación de envío de notificación
        print(f"📱 Notificación enviada a usuario {user_id}: {message}")
        
        # En producción, aquí se integraría con:
        # - AWS SNS, Azure Notification Hubs, o Firebase Cloud Messaging
        # - Servicios de SMS como Twilio
        # - Servicios de email como SendGrid
        
        return True
    
    def _format_transaction_message(self, transaction: Transaction) -> str:
        """Formatea mensaje de transacción"""
        if transaction.transaction_type == TransactionType.DEPOSIT:
            return f"Depósito de ${transaction.amount:.2f} procesado exitosamente"
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            return f"Retiro de ${transaction.amount:.2f} procesado exitosamente"
        elif transaction.transaction_type == TransactionType.TRANSFER:
            return f"Transferencia de ${transaction.amount:.2f} procesada exitosamente"
        else:
            return f"Transacción de ${transaction.amount:.2f} procesada exitosamente"

# =============================================================================
# 3. API GATEWAY Y CONTROLADORES
# =============================================================================

class BankingAPI:
    """API principal de la aplicación bancaria"""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.account_service = AccountService()
        self.transaction_service = TransactionService()
        self.notification_service = NotificationService()
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Autentica usuario y retorna token"""
        # Simulación de autenticación (en producción validaría contra base de datos)
        if email and password:
            user_id = str(uuid.uuid4())
            token = self.auth_service.generate_jwt_token(user_id)
            
            return {
                "success": True,
                "token": token,
                "user_id": user_id,
                "expires_in": 86400  # 24 horas
            }
        
        return {
            "success": False,
            "message": "Credenciales inválidas"
        }
    
    def get_account_balance(self, token: str, account_id: str) -> Dict[str, Any]:
        """Obtiene saldo de cuenta"""
        user_id = self.auth_service.verify_token(token)
        if not user_id:
            return {"success": False, "message": "Token inválido"}
        
        balance = self.account_service.get_account_balance(account_id)
        if balance is None:
            return {"success": False, "message": "Cuenta no encontrada"}
        
        return {
            "success": True,
            "balance": balance,
            "account_id": account_id
        }
    
    def process_transaction(self, token: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una transacción bancaria"""
        user_id = self.auth_service.verify_token(token)
        if not user_id:
            return {"success": False, "message": "Token inválido"}
        
        # Crear objeto transacción
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            from_account_id=transaction_data.get("from_account_id"),
            to_account_id=transaction_data.get("to_account_id"),
            amount=float(transaction_data["amount"]),
            transaction_type=TransactionType(transaction_data["type"]),
            status=TransactionStatus.PENDING,
            description=transaction_data.get("description", ""),
            created_at=datetime.now(),
            reference_number=transaction_data.get("reference_number")
        )
        
        # Procesar transacción
        result = self.transaction_service.process_transaction(transaction)
        
        # Enviar notificación si es exitosa
        if result["success"]:
            self.notification_service.send_transaction_notification(user_id, transaction)
        
        return result

# =============================================================================
# 4. CONFIGURACIÓN DE ARQUITECTURA CLOUD
# =============================================================================

class CloudArchitectureConfig:
    """Configuración de la arquitectura cloud híbrida"""
    
    def __init__(self):
        self.config = {
            "hybrid_cloud": {
                "public_cloud": {
                    "provider": "AWS/Azure/GCP",
                    "services": [
                        "API Gateway",
                        "Lambda Functions",
                        "DynamoDB/CosmosDB",
                        "S3/Blob Storage",
                        "CloudFront/CDN",
                        "SNS/Notification Hubs"
                    ]
                },
                "private_cloud": {
                    "provider": "On-premises/Private Cloud",
                    "services": [
                        "Core Banking System",
                        "Customer Database",
                        "Transaction Processing",
                        "Compliance & Audit Logs"
                    ]
                }
            },
            "serverless_functions": {
                "authentication": {
                    "runtime": "Python 3.9/Node.js 18",
                    "memory": "256 MB",
                    "timeout": "30 seconds",
                    "triggers": ["API Gateway", "Cognito"]
                },
                "account_management": {
                    "runtime": "Python 3.9",
                    "memory": "512 MB",
                    "timeout": "60 seconds",
                    "triggers": ["API Gateway", "DynamoDB Streams"]
                },
                "transaction_processing": {
                    "runtime": "Python 3.9",
                    "memory": "1024 MB",
                    "timeout": "120 seconds",
                    "triggers": ["API Gateway", "SQS"]
                },
                "notifications": {
                    "runtime": "Node.js 18",
                    "memory": "256 MB",
                    "timeout": "30 seconds",
                    "triggers": ["SNS", "EventBridge"]
                }
            },
            "security": {
                "encryption": {
                    "in_transit": "TLS 1.3",
                    "at_rest": "AES-256",
                    "key_management": "AWS KMS/Azure Key Vault"
                },
                "authentication": {
                    "method": "JWT + OAuth 2.0",
                    "mfa": "TOTP/SMS",
                    "session_timeout": "24 hours"
                },
                "compliance": {
                    "standards": ["PCI DSS", "SOX", "GDPR"],
                    "audit_logging": "CloudTrail/Azure Monitor",
                    "data_retention": "7 years"
                }
            },
            "scalability": {
                "auto_scaling": {
                    "min_capacity": 1,
                    "max_capacity": 1000,
                    "target_utilization": 70
                },
                "load_balancing": "Application Load Balancer",
                "caching": "Redis/ElastiCache",
                "cdn": "CloudFront/Azure CDN"
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración completa"""
        return self.config

# =============================================================================
# 5. DIAGRAMA ARQUITECTÓNICO EN MERMAID
# =============================================================================

def generate_architecture_diagram() -> str:
    """Genera diagrama de arquitectura en formato Mermaid"""
    
    diagram = """
graph TB
    %% Cliente Móvil
    subgraph "Cliente Móvil"
        MA[Mobile App<br/>iOS/Android]
    end
    
    %% Nube Pública
    subgraph "Nube Pública (AWS/Azure/GCP)"
        subgraph "API Layer"
            AG[API Gateway<br/>Rate Limiting<br/>Authentication]
            LB[Load Balancer<br/>SSL Termination]
        end
        
        subgraph "Serverless Functions"
            AUTH[Authentication<br/>Lambda/Azure Function<br/>JWT Generation]
            ACC[Account Management<br/>Lambda/Azure Function<br/>Balance Queries]
            TXN[Transaction Processing<br/>Lambda/Azure Function<br/>Payment Processing]
            NOT[Notifications<br/>Lambda/Azure Function<br/>SMS/Email/Push]
        end
        
        subgraph "Data Layer"
            DB[(DynamoDB/CosmosDB<br/>User Data<br/>Account Info)]
            CACHE[(Redis/ElastiCache<br/>Session Cache<br/>Rate Limiting)]
            S3[S3/Blob Storage<br/>Documents<br/>Audit Logs]
        end
        
        subgraph "Messaging & Events"
            SQS[SQS/Service Bus<br/>Transaction Queue]
            SNS[SNS/Notification Hub<br/>Event Broadcasting]
            EB[EventBridge<br/>Event Routing]
        end
        
        subgraph "Security & Monitoring"
            KMS[KMS/Key Vault<br/>Encryption Keys]
            CW[CloudWatch/Azure Monitor<br/>Logging & Metrics]
            WAF[WAF<br/>DDoS Protection]
        end
    end
    
    %% Nube Privada/On-Premises
    subgraph "Nube Privada/On-Premises"
        subgraph "Core Banking"
            CBS[Core Banking System<br/>Mainframe/Legacy]
            TPS[Transaction Processing<br/>Real-time Processing]
        end
        
        subgraph "Compliance & Audit"
            AUDIT[Audit System<br/>Compliance Logs]
            KYC[KYC System<br/>Identity Verification]
        end
        
        subgraph "Private Data"
            PDB[(Customer Database<br/>Sensitive Data<br/>PII)]
            COMP[(Compliance Database<br/>Regulatory Data)]
        end
    end
    
    %% Conexiones Cliente
    MA -->|HTTPS/TLS 1.3| AG
    MA -->|Push Notifications| SNS
    
    %% Conexiones API Gateway
    AG -->|Route| AUTH
    AG -->|Route| ACC
    AG -->|Route| TXN
    AG -->|Route| NOT
    
    %% Conexiones Serverless
    AUTH -->|Store Tokens| CACHE
    AUTH -->|User Data| DB
    
    ACC -->|Account Data| DB
    ACC -->|Cache| CACHE
    ACC -->|Query| CBS
    
    TXN -->|Queue| SQS
    TXN -->|Process| TPS
    TXN -->|Update| DB
    TXN -->|Notify| SNS
    
    NOT -->|Send| SNS
    NOT -->|Log| S3
    
    %% Conexiones Data
    DB -->|Encrypt| KMS
    CACHE -->|Encrypt| KMS
    S3 -->|Encrypt| KMS
    
    %% Conexiones Privadas
    CBS -->|Sync| PDB
    TPS -->|Audit| AUDIT
    KYC -->|Verify| PDB
    
    %% Conexiones Seguras
    AG -->|VPN/Tunnel| CBS
    TXN -->|Secure API| TPS
    ACC -->|Encrypted| PDB
    
    %% Monitoreo
    CW -->|Monitor| AUTH
    CW -->|Monitor| ACC
    CW -->|Monitor| TXN
    CW -->|Monitor| NOT
    CW -->|Monitor| CBS
    
    %% Seguridad
    WAF -->|Protect| AG
    
    %% Estilos
    classDef publicCloud fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef privateCloud fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef serverless fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef security fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class AG,LB,AUTH,ACC,TXN,NOT,DB,CACHE,S3,SQS,SNS,EB,KMS,CW,WAF publicCloud
    class CBS,TPS,AUDIT,KYC,PDB,COMP privateCloud
    class AUTH,ACC,TXN,NOT serverless
    class DB,CACHE,S3,PDB,COMP data
    class KMS,CW,WAF,AUDIT security
    """
    
    return diagram

# =============================================================================
# 6. EJEMPLO DE USO Y DEMOSTRACIÓN
# =============================================================================

def demonstrate_banking_system():
    """Demuestra el funcionamiento del sistema bancario"""
    
    print("🏦 DEMOSTRACIÓN DEL SISTEMA DE BANCA MÓVIL")
    print("=" * 50)
    
    # Inicializar servicios
    api = BankingAPI()
    config = CloudArchitectureConfig()
    
    # 1. Autenticación
    print("\n1. 🔐 AUTENTICACIÓN DE USUARIO")
    auth_result = api.authenticate_user("usuario@banco.com", "password123")
    print(f"Resultado: {json.dumps(auth_result, indent=2)}")
    
    if not auth_result["success"]:
        print("❌ Error en autenticación")
        return
    
    token = auth_result["token"]
    user_id = auth_result["user_id"]
    
    # 2. Crear cuenta
    print("\n2. 💳 CREACIÓN DE CUENTA")
    account = api.account_service.create_account(user_id, AccountType.CHECKING)
    print(f"Cuenta creada: {account.account_number}")
    print(f"Saldo inicial: ${account.balance}")
    
    # 3. Depósito
    print("\n3. 💰 PROCESAMIENTO DE DEPÓSITO")
    deposit_data = {
        "to_account_id": account.account_id,
        "amount": 1000.00,
        "type": "deposit",
        "description": "Depósito inicial"
    }
    
    deposit_result = api.process_transaction(token, deposit_data)
    print(f"Resultado del depósito: {json.dumps(deposit_result, indent=2)}")
    
    # 4. Consulta de saldo
    print("\n4. 📊 CONSULTA DE SALDO")
    balance_result = api.get_account_balance(token, account.account_id)
    print(f"Saldo actual: {json.dumps(balance_result, indent=2)}")
    
    # 5. Retiro
    print("\n5. 💸 PROCESAMIENTO DE RETIRO")
    withdrawal_data = {
        "from_account_id": account.account_id,
        "amount": 250.00,
        "type": "withdrawal",
        "description": "Retiro en cajero"
    }
    
    withdrawal_result = api.process_transaction(token, withdrawal_data)
    print(f"Resultado del retiro: {json.dumps(withdrawal_result, indent=2)}")
    
    # 6. Mostrar configuración de arquitectura
    print("\n6. ☁️ CONFIGURACIÓN DE ARQUITECTURA CLOUD")
    print("Configuración híbrida:")
    print(json.dumps(config.get_config()["hybrid_cloud"], indent=2))
    
    print("\n✅ Demostración completada exitosamente!")

# =============================================================================
# 7. FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal que ejecuta la demostración"""
    
    print("🚀 INICIANDO SISTEMA DE BANCA MÓVIL CON ARQUITECTURA CLOUD HÍBRIDA")
    print("=" * 80)
    
    # Mostrar diagrama de arquitectura
    print("\n📐 DIAGRAMA DE ARQUITECTURA:")
    print("=" * 40)
    print("(El diagrama Mermaid se puede visualizar en herramientas como Mermaid Live Editor)")
    print("\nCódigo del diagrama:")
    print(generate_architecture_diagram())
    
    # Ejecutar demostración
    demonstrate_banking_system()
    
    print("\n" + "=" * 80)
    print("📋 RESUMEN DE LA ARQUITECTURA:")
    print("=" * 80)
    print("""
    🏗️ ARQUITECTURA CLOUD HÍBRIDA:
    ├── 🌐 Nube Pública (AWS/Azure/GCP)
    │   ├── API Gateway + Load Balancer
    │   ├── Funciones Serverless (Lambda/Azure Functions)
    │   ├── Bases de Datos NoSQL (DynamoDB/CosmosDB)
    │   ├── Cache Redis/ElastiCache
    │   ├── Almacenamiento S3/Blob Storage
    │   ├── Colas de Mensajes (SQS/Service Bus)
    │   ├── Notificaciones (SNS/Notification Hubs)
    │   └── Monitoreo y Seguridad
    │
    └── 🏢 Nube Privada/On-Premises
        ├── Sistema Core Banking (Mainframe)
        ├── Procesamiento de Transacciones
        ├── Base de Datos de Clientes (PII)
        ├── Sistema de Cumplimiento (KYC)
        └── Auditoría y Logs de Compliance
    
    🔧 FUNCIONES SERVERLESS:
    ├── Authentication Service (JWT + OAuth 2.0)
    ├── Account Management Service
    ├── Transaction Processing Service
    └── Notification Service (SMS/Email/Push)
    
    🔒 SEGURIDAD:
    ├── Encriptación TLS 1.3 en tránsito
    ├── Encriptación AES-256 en reposo
    ├── Gestión de claves con KMS/Key Vault
    ├── Autenticación multifactor (MFA)
    ├── WAF para protección DDoS
    └── Cumplimiento PCI DSS, SOX, GDPR
    
    📈 ESCALABILIDAD:
    ├── Auto-scaling de funciones serverless
    ├── Load balancing automático
    ├── Cache distribuido
    ├── CDN para contenido estático
    └── Monitoreo en tiempo real
    """)

if __name__ == "__main__":
    main()
