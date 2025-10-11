import re
import argparse
import json
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class HardwareSpecs:
    """Especificaciones de hardware para clasificación detallada."""
    processor_cores: Optional[int] = None
    processor_speed_ghz: Optional[float] = None
    memory_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    storage_type: Optional[str] = None  # 'ssd', 'hdd', 'nvme'
    
    def __post_init__(self):
        """Validar las especificaciones de hardware."""
        if self.processor_cores is not None and self.processor_cores <= 0:
            raise ValueError("El número de núcleos del procesador debe ser mayor a 0")
        if self.processor_speed_ghz is not None and self.processor_speed_ghz <= 0:
            raise ValueError("La velocidad del procesador debe ser mayor a 0")
        if self.memory_gb is not None and self.memory_gb <= 0:
            raise ValueError("La memoria debe ser mayor a 0 GB")
        if self.storage_gb is not None and self.storage_gb <= 0:
            raise ValueError("El almacenamiento debe ser mayor a 0 GB")
        if self.storage_type is not None and self.storage_type not in ['ssd', 'hdd', 'nvme']:
            raise ValueError("El tipo de almacenamiento debe ser 'ssd', 'hdd' o 'nvme'")

class CloudServiceClassifier:
    """
    Clasificador de servicios en la nube que categoriza texto en IaaS, PaaS, SaaS o FaaS
    basándose en palabras clave y patrones específicos, incluyendo especificaciones de hardware.
    """
    
    def __init__(self):
        # Definir palabras clave para cada categoría
        self.keywords = {
            'IaaS': [
                'infrastructure as a service', 'infraestructura como servicio',
                'virtual machine', 'máquina virtual', 'vm', 'ec2', 'compute engine',
                'storage', 'almacenamiento', 'network', 'red', 'load balancer',
                'firewall', 'cortafuegos', 'server', 'servidor', 'hardware',
                'cpu', 'ram', 'memory', 'memoria', 'disk', 'disco', 'block storage',
                'object storage', 'file storage', 'vpc', 'subnet', 'ip address',
                'elastic ip', 'auto scaling', 'auto scaling group', 'processor',
                'procesador', 'core', 'núcleo', 'ghz', 'gigahertz', 'ssd', 'hdd',
                'nvme', 'gigabyte', 'gb', 'terabyte', 'tb'
            ],
            'PaaS': [
                'platform as a service', 'plataforma como servicio',
                'app engine', 'elastic beanstalk', 'heroku', 'openshift',
                'deployment', 'despliegue', 'runtime', 'entorno de ejecución',
                'framework', 'marco de trabajo', 'middleware', 'software intermedio',
                'database service', 'servicio de base de datos', 'rds', 'cloud sql',
                'cache', 'caché', 'message queue', 'cola de mensajes', 'sqs',
                'api gateway', 'puerta de enlace api', 'container', 'contenedor',
                'kubernetes', 'docker', 'orchestration', 'orquestación'
            ],
            'SaaS': [
                'software as a service', 'software como servicio',
                'application', 'aplicación', 'web app', 'aplicación web',
                'crm', 'erp', 'email', 'correo electrónico', 'office 365',
                'google workspace', 'salesforce', 'dropbox', 'box', 'slack',
                'zoom', 'teams', 'collaboration', 'colaboración', 'productivity',
                'productividad', 'business software', 'software empresarial',
                'subscription', 'suscripción', 'license', 'licencia', 'user',
                'usuario', 'dashboard', 'panel de control', 'analytics', 'análisis'
            ],
            'FaaS': [
                'function as a service', 'función como servicio',
                'serverless', 'sin servidor', 'lambda', 'cloud functions',
                'azure functions', 'google cloud functions', 'openwhisk',
                'function', 'función', 'event-driven', 'dirigido por eventos',
                'trigger', 'disparador', 'webhook', 'api endpoint', 'endpoint api',
                'microservice', 'microservicio', 'stateless', 'sin estado',
                'cold start', 'inicio en frío', 'timeout', 'tiempo de espera',
                'execution time', 'tiempo de ejecución', 'invocation', 'invocación'
            ]
        }
        
        # Patrones regex para cada categoría
        self.patterns = {
            'IaaS': [
                r'\b(ec2|compute engine|virtual machine|vm)\b',
                r'\b(storage|block storage|object storage)\b',
                r'\b(network|vpc|subnet|load balancer)\b',
                r'\b(server|hardware|cpu|ram|memory)\b',
                r'\b(\d+)\s*(core|núcleo|cores|núcleos)\b',
                r'\b(\d+(?:\.\d+)?)\s*(ghz|gigahertz)\b',
                r'\b(\d+)\s*(gb|gigabyte|gigabytes)\b',
                r'\b(\d+)\s*(tb|terabyte|terabytes)\b',
                r'\b(ssd|hdd|nvme)\b'
            ],
            'PaaS': [
                r'\b(app engine|elastic beanstalk|heroku|openshift)\b',
                r'\b(database|rds|cloud sql|cache)\b',
                r'\b(container|kubernetes|docker|orchestration)\b',
                r'\b(api gateway|middleware|framework)\b'
            ],
            'SaaS': [
                r'\b(crm|erp|office 365|google workspace)\b',
                r'\b(salesforce|dropbox|slack|zoom|teams)\b',
                r'\b(web app|application|subscription|license)\b',
                r'\b(collaboration|productivity|business software)\b'
            ],
            'FaaS': [
                r'\b(lambda|cloud functions|azure functions)\b',
                r'\b(serverless|function as a service)\b',
                r'\b(event-driven|trigger|webhook)\b',
                r'\b(microservice|stateless|cold start)\b'
            ]
        }
        
        # Configuración de hardware por defecto
        self.default_hardware_specs = HardwareSpecs()
    
    def set_hardware_specs(self, specs: HardwareSpecs):
        """
        Define las especificaciones de hardware para la clasificación.
        
        Args:
            specs (HardwareSpecs): Especificaciones de hardware
        """
        self.default_hardware_specs = specs
    
    def extract_hardware_info(self, text: str) -> HardwareSpecs:
        """
        Extrae información de hardware del texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            HardwareSpecs: Especificaciones de hardware encontradas
        """
        text_lower = text.lower()
        
        # Extraer núcleos del procesador
        processor_cores = None
        core_match = re.search(r'(\d+)\s*(core|núcleo|cores|núcleos)', text_lower)
        if core_match:
            processor_cores = int(core_match.group(1))
        
        # Extraer velocidad del procesador
        processor_speed = None
        speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(ghz|gigahertz)', text_lower)
        if speed_match:
            processor_speed = float(speed_match.group(1))
        
        # Extraer memoria
        memory_gb = None
        memory_match = re.search(r'(\d+)\s*(gb|gigabyte|gigabytes)\s*(?:ram|memory|memoria)', text_lower)
        if memory_match:
            memory_gb = int(memory_match.group(1))
        
        # Extraer almacenamiento
        storage_gb = None
        storage_match = re.search(r'(\d+)\s*(gb|gigabyte|gigabytes|tb|terabyte|terabytes)', text_lower)
        if storage_match:
            value = int(storage_match.group(1))
            unit = storage_match.group(2)
            if unit in ['tb', 'terabyte', 'terabytes']:
                storage_gb = value * 1024
            else:
                storage_gb = value
        
        # Extraer tipo de almacenamiento
        storage_type = None
        if 'ssd' in text_lower:
            storage_type = 'ssd'
        elif 'nvme' in text_lower:
            storage_type = 'nvme'
        elif 'hdd' in text_lower or 'hard disk' in text_lower:
            storage_type = 'hdd'
        
        return HardwareSpecs(
            processor_cores=processor_cores,
            processor_speed_ghz=processor_speed,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            storage_type=storage_type
        )
    
    def classify_by_hardware(self, specs: HardwareSpecs) -> Dict[str, float]:
        """
        Clasifica basándose en especificaciones de hardware.
        
        Args:
            specs (HardwareSpecs): Especificaciones de hardware
            
        Returns:
            Dict[str, float]: Probabilidades basadas en hardware
        """
        scores = {'IaaS': 0, 'PaaS': 0, 'SaaS': 0, 'FaaS': 0}
        
        # Si hay especificaciones de hardware, es más probable que sea IaaS
        if any([specs.processor_cores, specs.processor_speed_ghz, specs.memory_gb, specs.storage_gb]):
            scores['IaaS'] += 3
        
        # Procesador específico sugiere IaaS
        if specs.processor_cores:
            if specs.processor_cores >= 8:
                scores['IaaS'] += 2
            elif specs.processor_cores >= 4:
                scores['IaaS'] += 1
            else:
                scores['PaaS'] += 1
        
        # Memoria específica sugiere IaaS
        if specs.memory_gb:
            if specs.memory_gb >= 32:
                scores['IaaS'] += 2
            elif specs.memory_gb >= 16:
                scores['IaaS'] += 1
            else:
                scores['PaaS'] += 1
        
        # Almacenamiento específico sugiere IaaS
        if specs.storage_gb:
            if specs.storage_gb >= 1000:  # 1TB
                scores['IaaS'] += 2
            elif specs.storage_gb >= 100:
                scores['IaaS'] += 1
            else:
                scores['PaaS'] += 1
        
        # Tipo de almacenamiento
        if specs.storage_type:
            if specs.storage_type in ['ssd', 'nvme']:
                scores['IaaS'] += 1
            else:
                scores['IaaS'] += 0.5
        
        # Calcular probabilidades
        total = sum(scores.values())
        if total == 0:
            return {category: 0.25 for category in scores.keys()}
        
        return {category: score / total for category, score in scores.items()}
    
    def validate_input(self, text: str) -> Dict[str, bool]:
        """
        Valida el texto de entrada antes de la clasificación.
        
        Args:
            text (str): Texto a validar
            
        Returns:
            Dict[str, bool]: Diccionario con el resultado de la validación
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Verificar si el texto es None
        if text is None:
            validation_result['is_valid'] = False
            validation_result['errors'].append("El texto no puede ser None")
            return validation_result
        
        # Verificar si el texto es una cadena
        if not isinstance(text, str):
            validation_result['is_valid'] = False
            validation_result['errors'].append("El texto debe ser una cadena de caracteres")
            return validation_result
        
        # Verificar si el texto está vacío
        if not text.strip():
            validation_result['is_valid'] = False
            validation_result['errors'].append("El texto no puede estar vacío")
            return validation_result
        
        # Verificar longitud mínima
        if len(text.strip()) < 3:
            validation_result['warnings'].append("El texto es muy corto, puede afectar la precisión de la clasificación")
        
        # Verificar longitud máxima
        if len(text) > 10000:
            validation_result['warnings'].append("El texto es muy largo, se procesarán solo los primeros 10000 caracteres")
        
        # Verificar caracteres especiales o no válidos
        invalid_chars = re.findall(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}\"\']', text)
        if invalid_chars:
            validation_result['warnings'].append(f"El texto contiene caracteres especiales: {set(invalid_chars)}")
        
        # Verificar si el texto contiene solo números
        if text.strip().replace('.', '').replace(',', '').replace(' ', '').isdigit():
            validation_result['warnings'].append("El texto contiene solo números, puede afectar la clasificación")
        
        return validation_result
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocesa el texto para mejorar la clasificación.
        
        Args:
            text (str): Texto a preprocesar
            
        Returns:
            str: Texto preprocesado
        """
        # Limitar longitud si es muy largo
        if len(text) > 10000:
            text = text[:10000]
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convertir a minúsculas
        text = text.lower()
        
        return text
    
    def classify_text(self, text: str, hardware_specs: Optional[HardwareSpecs] = None) -> Dict[str, float]:
        """
        Clasifica el texto de entrada y retorna las probabilidades para cada categoría.
        
        Args:
            text (str): Texto a clasificar
            hardware_specs (HardwareSpecs, optional): Especificaciones de hardware adicionales
            
        Returns:
            Dict[str, float]: Diccionario con categorías y sus probabilidades
        """
        # Validar entrada
        validation = self.validate_input(text)
        if not validation['is_valid']:
            raise ValueError(f"Error de validación: {'; '.join(validation['errors'])}")
        
        # Mostrar advertencias si las hay
        if validation['warnings']:
            print("Advertencias de validación:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # Preprocesar texto
        text_processed = self.preprocess_text(text)
        
        # Extraer información de hardware del texto
        extracted_specs = self.extract_hardware_info(text_processed)
        
        # Usar especificaciones proporcionadas o extraídas
        final_specs = hardware_specs if hardware_specs else extracted_specs
        
        # Contar coincidencias de palabras clave
        keyword_scores = {}
        for category, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_processed:
                    score += 1
            keyword_scores[category] = score
        
        # Contar coincidencias de patrones regex
        pattern_scores = {}
        for category, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_processed))
                score += matches
            pattern_scores[category] = score
        
        # Combinar puntuaciones de texto
        text_scores = {}
        for category in self.keywords.keys():
            text_scores[category] = keyword_scores[category] + pattern_scores[category]
        
        # Obtener puntuaciones de hardware
        hardware_scores = self.classify_by_hardware(final_specs)
        
        # Combinar puntuaciones (70% texto, 30% hardware)
        total_scores = {}
        for category in self.keywords.keys():
            text_weight = 0.7
            hardware_weight = 0.3
            total_scores[category] = (text_scores[category] * text_weight + 
                                    hardware_scores[category] * hardware_weight)
        
        # Calcular probabilidades
        total = sum(total_scores.values())
        if total == 0:
            # Si no hay coincidencias, asignar probabilidades iguales
            return {category: 0.25 for category in self.keywords.keys()}
        
        probabilities = {}
        for category, score in total_scores.items():
            probabilities[category] = score / total
        
        return probabilities
    
    def get_primary_classification(self, text: str, hardware_specs: Optional[HardwareSpecs] = None) -> Tuple[str, float]:
        """
        Obtiene la clasificación principal del texto.
        
        Args:
            text (str): Texto a clasificar
            hardware_specs (HardwareSpecs, optional): Especificaciones de hardware adicionales
            
        Returns:
            Tuple[str, float]: Tupla con la categoría principal y su probabilidad
        """
        probabilities = self.classify_text(text, hardware_specs)
        primary_category = max(probabilities, key=probabilities.get)
        primary_probability = probabilities[primary_category]
        return primary_category, primary_probability
    
    def classify_with_details(self, text: str, hardware_specs: Optional[HardwareSpecs] = None) -> Dict:
        """
        Clasifica el texto con detalles adicionales.
        
        Args:
            text (str): Texto a clasificar
            hardware_specs (HardwareSpecs, optional): Especificaciones de hardware adicionales
            
        Returns:
            Dict: Diccionario con clasificación y detalles
        """
        # Validar entrada
        validation = self.validate_input(text)
        if not validation['is_valid']:
            raise ValueError(f"Error de validación: {'; '.join(validation['errors'])}")
        
        # Preprocesar texto
        text_processed = self.preprocess_text(text)
        
        # Extraer información de hardware
        extracted_specs = self.extract_hardware_info(text_processed)
        final_specs = hardware_specs if hardware_specs else extracted_specs
        
        probabilities = self.classify_text(text, hardware_specs)
        primary_category, primary_probability = self.get_primary_classification(text, hardware_specs)
        
        # Encontrar palabras clave encontradas
        found_keywords = {}
        
        for category, keywords in self.keywords.items():
            found_keywords[category] = []
            for keyword in keywords:
                if keyword in text_processed:
                    found_keywords[category].append(keyword)
        
        return {
            'text': text,
            'processed_text': text_processed,
            'primary_classification': primary_category,
            'confidence': primary_probability,
            'probabilities': probabilities,
            'found_keywords': found_keywords,
            'validation': validation,
            'hardware_specs': final_specs
        }


def parse_arguments():
    """
    Configura y parsea los argumentos de línea de comando.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description='Clasificador de servicios en la nube (IaaS, PaaS, SaaS, FaaS)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python cloud_classifier.py "Amazon EC2 provides virtual machines"
  python cloud_classifier.py -t "AWS Lambda executes code" --format json
  python cloud_classifier.py -f input.txt --cores 8 --memory 32 --storage 1000
  python cloud_classifier.py --demo
        """
    )
    
    # Grupo para entrada de texto
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-t', '--text',
        type=str,
        help='Texto a clasificar'
    )
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='Archivo de texto a clasificar'
    )
    input_group.add_argument(
        '--demo',
        action='store_true',
        help='Ejecutar ejemplos de demostración'
    )
    
    # Especificaciones de hardware
    hardware_group = parser.add_argument_group('Especificaciones de Hardware')
    hardware_group.add_argument(
        '--cores',
        type=int,
        help='Número de núcleos del procesador'
    )
    hardware_group.add_argument(
        '--speed',
        type=float,
        help='Velocidad del procesador en GHz'
    )
    hardware_group.add_argument(
        '--memory',
        type=int,
        help='Memoria RAM en GB'
    )
    hardware_group.add_argument(
        '--storage',
        type=int,
        help='Almacenamiento en GB'
    )
    hardware_group.add_argument(
        '--storage-type',
        choices=['ssd', 'hdd', 'nvme'],
        help='Tipo de almacenamiento'
    )
    
    # Opciones de salida
    output_group = parser.add_argument_group('Opciones de Salida')
    output_group.add_argument(
        '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Formato de salida (default: text)'
    )
    output_group.add_argument(
        '--output',
        type=str,
        help='Archivo de salida (si no se especifica, se usa stdout)'
    )
    output_group.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar información detallada'
    )
    output_group.add_argument(
        '--quiet',
        action='store_true',
        help='Mostrar solo la clasificación principal'
    )
    
    return parser.parse_args()


def create_hardware_specs(args):
    """
    Crea especificaciones de hardware a partir de los argumentos.
    
    Args:
        args: Argumentos parseados
        
    Returns:
        HardwareSpecs: Especificaciones de hardware
    """
    if any([args.cores, args.speed, args.memory, args.storage, args.storage_type]):
        return HardwareSpecs(
            processor_cores=args.cores,
            processor_speed_ghz=args.speed,
            memory_gb=args.memory,
            storage_gb=args.storage,
            storage_type=args.storage_type
        )
    return None


def format_output(result, output_format, verbose=False, quiet=False):
    """
    Formatea la salida según el formato especificado.
    
    Args:
        result: Resultado de la clasificación
        output_format: Formato de salida
        verbose: Mostrar información detallada
        quiet: Mostrar solo clasificación principal
        
    Returns:
        str: Salida formateada
    """
    if output_format == 'json':
        # Preparar datos para JSON
        json_data = {
            'text': result['text'],
            'primary_classification': result['primary_classification'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities']
        }
        
        if verbose:
            json_data.update({
                'hardware_specs': {
                    'processor_cores': result['hardware_specs'].processor_cores,
                    'processor_speed_ghz': result['hardware_specs'].processor_speed_ghz,
                    'memory_gb': result['hardware_specs'].memory_gb,
                    'storage_gb': result['hardware_specs'].storage_gb,
                    'storage_type': result['hardware_specs'].storage_type
                },
                'found_keywords': result['found_keywords'],
                'validation': result['validation']
            })
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    elif output_format == 'csv':
        # Formato CSV simple
        if quiet:
            return f"{result['primary_classification']},{result['confidence']:.4f}"
        else:
            return f"{result['text'][:50]},{result['primary_classification']},{result['confidence']:.4f},{result['probabilities']['IaaS']:.4f},{result['probabilities']['PaaS']:.4f},{result['probabilities']['SaaS']:.4f},{result['probabilities']['FaaS']:.4f}"
    
    else:  # text format
        output_lines = []
        
        if not quiet:
            output_lines.append(f"Texto: {result['text']}")
            output_lines.append(f"Clasificación principal: {result['primary_classification']}")
            output_lines.append(f"Confianza: {result['confidence']:.2%}")
            
            if verbose:
                output_lines.append("\nProbabilidades:")
                for category, prob in result['probabilities'].items():
                    output_lines.append(f"  {category}: {prob:.2%}")
                
                # Mostrar especificaciones de hardware
                if result['hardware_specs']:
                    specs = result['hardware_specs']
                    output_lines.append("\nEspecificaciones de hardware:")
                    if specs.processor_cores:
                        output_lines.append(f"  Procesador: {specs.processor_cores} núcleos")
                    if specs.processor_speed_ghz:
                        output_lines.append(f"  Velocidad: {specs.processor_speed_ghz} GHz")
                    if specs.memory_gb:
                        output_lines.append(f"  Memoria: {specs.memory_gb} GB")
                    if specs.storage_gb:
                        output_lines.append(f"  Almacenamiento: {specs.storage_gb} GB")
                    if specs.storage_type:
                        output_lines.append(f"  Tipo: {specs.storage_type.upper()}")
                
                output_lines.append("\nPalabras clave encontradas:")
                for category, keywords in result['found_keywords'].items():
                    if keywords:
                        output_lines.append(f"  {category}: {', '.join(keywords[:3])}...")
        else:
            output_lines.append(f"{result['primary_classification']} ({result['confidence']:.2%})")
        
        return '\n'.join(output_lines)


def run_demo():
    """
    Ejecuta ejemplos de demostración.
    """
    classifier = CloudServiceClassifier()
    
    examples = [
        "Amazon EC2 provides virtual machines with scalable compute capacity",
        "Google App Engine allows you to deploy web applications easily",
        "Salesforce CRM helps manage customer relationships",
        "AWS Lambda executes code in response to events without provisioning servers",
        "EC2 instance with 8 cores, 32GB RAM, and 1TB SSD storage"
    ]
    
    print("=== Demostración del Clasificador de Servicios en la Nube ===\n")
    
    for i, example in enumerate(examples, 1):
        print(f"Ejemplo {i}:")
        print(f"Texto: {example}")
        
        try:
            result = classifier.classify_with_details(example)
            print(f"Clasificación: {result['primary_classification']} ({result['confidence']:.2%})")
            print("-" * 60)
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 60)


def main():
    """
    Función principal que maneja la línea de comando.
    """
    args = parse_arguments()
    
    # Ejecutar demostración si se solicita
    if args.demo:
        run_demo()
        return
    
    # Crear clasificador
    classifier = CloudServiceClassifier()
    
    # Crear especificaciones de hardware si se proporcionan
    hardware_specs = create_hardware_specs(args)
    
    # Obtener texto a clasificar
    if args.text:
        text = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{args.file}'")
            sys.exit(1)
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
            sys.exit(1)
    
    # Clasificar texto
    try:
        result = classifier.classify_with_details(text, hardware_specs)
        
        # Formatear salida
        output = format_output(result, args.format, args.verbose, args.quiet)
        
        # Escribir salida
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                if not args.quiet:
                    print(f"Resultado guardado en: {args.output}")
            except Exception as e:
                print(f"Error al escribir archivo: {e}")
                sys.exit(1)
        else:
            print(output)
            
    except ValueError as e:
        print(f"Error de validación: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
