#!/usr/bin/env python3
"""
Programa de comparación de rendimiento entre Redis y MariaDB
Autor: Asistente IA
Descripción: Compara tiempos de inserción y lectura entre Redis y MariaDB
"""

import redis
import pymysql
import time
import hashlib
import sys
from typing import Dict, Tuple, Any

class DatabaseComparison:
    def __init__(self):
        """Inicializa las conexiones a Redis y MariaDB"""
        self.redis_client = None
        self.mysql_connection = None
        self.setup_connections()
    
    def setup_connections(self):
        """Configura las conexiones a las bases de datos"""
        try:
            # Conexión a Redis
            print("🔗 Conectando a Redis...")
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()  # Test de conexión
            print("✅ Conexión a Redis exitosa")
            
            # Conexión a MariaDB
            print("🔗 Conectando a MariaDB...")
            self.mysql_connection = pymysql.connect(
                host='localhost',
                user='libros_user',
                password='666',
                database='Libros',
                charset='utf8mb4'
            )
            print("✅ Conexión a MariaDB exitosa")
            
        except Exception as e:
            print(f"❌ Error en las conexiones: {e}")
            sys.exit(1)
    
    def get_user_data(self) -> Dict[str, str]:
        """Solicita datos del usuario"""
        print("\n" + "="*50)
        print("📝 INGRESO DE DATOS DEL USUARIO")
        print("="*50)
        
        username = input("Ingresa tu username: ").strip()
        email = input("Ingresa tu email: ").strip()
        password = input("Ingresa tu password: ").strip()
        
        # Crear hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        return {
            'username': username,
            'email': email,
            'password_hash': password_hash
        }
    
    def show_redis_functions(self):
        """Muestra las funciones de Redis que se están utilizando"""
        print("\n🔧 FUNCIONES DE REDIS UTILIZADAS")
        print("="*50)
        
        redis_functions = [
            "🔹 redis.Redis() - Crear conexión al servidor Redis",
            "🔹 client.ping() - Verificar conexión con el servidor",
            "🔹 client.hset() - Almacenar datos como hash (estructura clave-valor)",
            "🔹 client.hgetall() - Recuperar todos los campos de un hash",
            "🔹 client.delete() - Eliminar una clave y sus datos",
            "🔹 client.close() - Cerrar conexión con Redis"
        ]
        
        for func in redis_functions:
            print(func)
        
        print("\n📋 EXPLICACIÓN DE LAS FUNCIONES:")
        print("• hset(): Almacena múltiples campos en un hash de Redis")
        print("• hgetall(): Recupera todos los campos y valores de un hash")
        print("• delete(): Elimina completamente una clave de Redis")
        print("• Los hashes en Redis son ideales para objetos estructurados")
    
    def redis_operations(self, user_data: Dict[str, str]) -> Tuple[float, float]:
        """Realiza operaciones en Redis y mide el tiempo"""
        print("\n🔴 OPERACIONES EN REDIS")
        print("-" * 30)
        
        # Mostrar funciones de Redis utilizadas
        self.show_redis_functions()
        
        # Inserción en Redis usando hash
        print("\n📝 Insertando datos en Redis...")
        print("🔧 Usando: redis_client.hset() con mapping")
        start_time = time.time()
        
        # Usar hash de Redis para almacenar datos del usuario
        user_id = f"user:{user_data['username']}"
        self.redis_client.hset(user_id, mapping={
            'username': user_data['username'],
            'email': user_data['email'],
            'password_hash': user_data['password_hash'],
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        insert_time = time.time() - start_time
        print(f"✅ Datos insertados en Redis en {insert_time:.6f} segundos")
        
        # Lectura desde Redis
        print("\n📖 Leyendo datos desde Redis...")
        print("🔧 Usando: redis_client.hgetall()")
        start_time = time.time()
        
        retrieved_data = self.redis_client.hgetall(user_id)
        
        read_time = time.time() - start_time
        print(f"✅ Datos leídos desde Redis en {read_time:.6f} segundos")
        print(f"📊 Datos recuperados: {retrieved_data}")
        
        return insert_time, read_time
    
    def mariadb_operations(self, user_data: Dict[str, str]) -> Tuple[float, float]:
        """Realiza operaciones en MariaDB y mide el tiempo"""
        print("\n🔵 OPERACIONES EN MARIADB")
        print("-" * 30)
        
        cursor = self.mysql_connection.cursor()
        
        try:
            # Inserción en MariaDB
            print("📝 Insertando datos en MariaDB...")
            start_time = time.time()
            
            insert_query = """
            INSERT INTO users (username, email, password_hash) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_data['username'],
                user_data['email'],
                user_data['password_hash']
            ))
            self.mysql_connection.commit()
            
            insert_time = time.time() - start_time
            print(f"✅ Datos insertados en MariaDB en {insert_time:.6f} segundos")
            
            # Lectura desde MariaDB
            print("📖 Leyendo datos desde MariaDB...")
            start_time = time.time()
            
            select_query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(select_query, (user_data['username'],))
            result = cursor.fetchone()
            
            read_time = time.time() - start_time
            print(f"✅ Datos leídos desde MariaDB en {read_time:.6f} segundos")
            
            if result:
                print(f"📊 Datos recuperados: ID={result[0]}, Username={result[1]}, Email={result[2]}, Password_hash={result[3][:20]}..., Created_at={result[4]}")
            
            return insert_time, read_time
            
        except Exception as e:
            print(f"❌ Error en MariaDB: {e}")
            return 0, 0
        finally:
            cursor.close()
    
    def compare_performance(self, redis_times: Tuple[float, float], mariadb_times: Tuple[float, float]):
        """Compara y muestra los resultados de rendimiento"""
        print("\n" + "="*60)
        print("📊 COMPARACIÓN DE RENDIMIENTO")
        print("="*60)
        
        redis_insert, redis_read = redis_times
        mariadb_insert, mariadb_read = mariadb_times
        
        print(f"\n🔴 REDIS:")
        print(f"   Inserción: {redis_insert:.6f} segundos")
        print(f"   Lectura:   {redis_read:.6f} segundos")
        print(f"   Total:     {redis_insert + redis_read:.6f} segundos")
        
        print(f"\n🔵 MARIADB:")
        print(f"   Inserción: {mariadb_insert:.6f} segundos")
        print(f"   Lectura:   {mariadb_read:.6f} segundos")
        print(f"   Total:     {mariadb_insert + mariadb_read:.6f} segundos")
        
        # Calcular cuántas veces más lento es MariaDB
        if redis_insert > 0 and mariadb_insert > 0:
            insert_ratio = mariadb_insert / redis_insert
            print(f"\n⚡ MARIADB es {insert_ratio:.2f}x más lento que Redis en INSERCIÓN")
        
        if redis_read > 0 and mariadb_read > 0:
            read_ratio = mariadb_read / redis_read
            print(f"⚡ MARIADB es {read_ratio:.2f}x más lento que Redis en LECTURA")
        
        total_redis = redis_insert + redis_read
        total_mariadb = mariadb_insert + mariadb_read
        
        if total_redis > 0 and total_mariadb > 0:
            total_ratio = total_mariadb / total_redis
            print(f"⚡ MARIADB es {total_ratio:.2f}x más lento que Redis en TOTAL")
    
    def cleanup_data(self, username: str):
        """Limpia los datos de ambas bases de datos"""
        print("\n🧹 LIMPIANDO DATOS...")
        print("-" * 30)
        
        try:
            # Limpiar Redis
            print("🔧 Usando: redis_client.delete()")
            user_id = f"user:{username}"
            self.redis_client.delete(user_id)
            print("✅ Datos eliminados de Redis")
            
            # Limpiar MariaDB
            print("🔧 Usando: cursor.execute() con DELETE SQL")
            cursor = self.mysql_connection.cursor()
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            self.mysql_connection.commit()
            cursor.close()
            print("✅ Datos eliminados de MariaDB")
            
        except Exception as e:
            print(f"❌ Error durante la limpieza: {e}")
    
    def explain_performance_differences(self):
        """Explica por qué Redis es más rápido que MariaDB"""
        print("\n" + "="*60)
        print("🧠 ¿POR QUÉ REDIS ES MÁS RÁPIDO QUE MARIADB?")
        print("="*60)
        
        explanations = [
            "🔴 REDIS (In-Memory Database):",
            "   • Almacena datos en RAM (memoria principal)",
            "   • No hay overhead de disco duro",
            "   • Estructuras de datos optimizadas",
            "   • Sin transacciones ACID complejas",
            "   • Protocolo simple y eficiente",
            "",
            "🔵 MARIADB (Disk-Based Database):",
            "   • Almacena datos en disco duro",
            "   • Overhead de I/O de disco",
            "   • Transacciones ACID completas",
            "   • Índices y optimizaciones complejas",
            "   • Protocolo SQL más pesado",
            "",
            "📈 VENTAJAS DE REDIS:",
            "   • Acceso directo a memoria (nanosegundos vs milisegundos)",
            "   • Sin parsing de SQL",
            "   • Estructuras de datos nativas",
            "   • Menos overhead de protocolo",
            "",
            "📉 DESVENTAJAS DE REDIS:",
            "   • Datos volátiles (se pierden al reiniciar)",
            "   • Menos funcionalidades de consulta",
            "   • Limitado por la RAM disponible",
            "",
            "🎯 CONCLUSIÓN:",
            "   Redis es ideal para caché, sesiones y datos temporales",
            "   MariaDB es ideal para datos persistentes y consultas complejas"
        ]
        
        for explanation in explanations:
            print(explanation)
    
    def close_connections(self):
        """Cierra las conexiones"""
        try:
            if self.redis_client:
                self.redis_client.close()
            if self.mysql_connection:
                self.mysql_connection.close()
            print("\n✅ Conexiones cerradas correctamente")
        except Exception as e:
            print(f"❌ Error cerrando conexiones: {e}")

def main():
    """Función principal del programa"""
    print("🚀 COMPARACIÓN DE RENDIMIENTO: REDIS vs MARIADB")
    print("="*60)
    
    db_comparison = DatabaseComparison()
    
    try:
        # Ciclo principal para múltiples usuarios
        while True:
            print("\n" + "="*60)
            print("🔄 NUEVA COMPARACIÓN DE RENDIMIENTO")
            print("="*60)
            
            # Obtener datos del usuario
            user_data = db_comparison.get_user_data()
            
            # Realizar operaciones y medir tiempos
            redis_times = db_comparison.redis_operations(user_data)
            mariadb_times = db_comparison.mariadb_operations(user_data)
            
            # Comparar rendimiento
            db_comparison.compare_performance(redis_times, mariadb_times)
            
            # Explicar diferencias (solo en la primera iteración)
            if not hasattr(main, 'explanation_shown'):
                db_comparison.explain_performance_differences()
                main.explanation_shown = True
            
            # Limpiar datos
            db_comparison.cleanup_data(user_data['username'])
            
            # Preguntar si quiere continuar
            print("\n" + "="*50)
            print("🤔 ¿DESEA REALIZAR OTRA COMPARACIÓN?")
            print("="*50)
            
            while True:
                continue_choice = input("¿Continuar con otro usuario? (s/n): ").strip().lower()
                if continue_choice in ['s', 'si', 'sí', 'y', 'yes']:
                    break
                elif continue_choice in ['n', 'no']:
                    print("\n👋 ¡Gracias por usar el programa!")
                    return
                else:
                    print("❌ Por favor, ingresa 's' para sí o 'n' para no")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        db_comparison.close_connections()
        print("\n👋 ¡Programa finalizado!")

if __name__ == "__main__":
    main()
