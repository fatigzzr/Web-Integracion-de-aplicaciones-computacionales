// ===== FUNCIONES GLOBALES PARA TODO EL SITIO WEB =====

// Función para toggle del código (usado en ejercicio1.html)
function toggleCode() {
    const codePreview = document.getElementById('codePreview');
    const toggleIcon = document.querySelector('.toggle-icon-top');
    const toggleText = document.querySelector('.toggle-text-top');
    
    if (codePreview && toggleIcon && toggleText) {
        if (codePreview.classList.contains('code-collapsed')) {
            // Expandir código
            codePreview.classList.remove('code-collapsed');
            toggleIcon.classList.add('expanded');
            toggleText.textContent = 'Compactar';
        } else {
            // Compactar código
            codePreview.classList.add('code-collapsed');
            toggleIcon.classList.remove('expanded');
            toggleText.textContent = 'Expandir';
        }
    }
}

// Función para abrir modal de imágenes (usado en todas las páginas con imágenes)
function openImageModal(src) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    if (modal && modalImg) {
        modalImg.src = src;
        modal.style.display = 'flex';
        modal.style.justifyContent = 'center';
        modal.style.alignItems = 'center';
        
        // Asegurar que la imagen se cargue correctamente
        modalImg.onload = function() {
            // Forzar reflow para asegurar que los estilos se apliquen
            modal.offsetHeight;
        };
    }
}

// Función para abrir modal de PDF (usado en tarea1.html)
function openPDFModal(pdfSrc) {
    const modal = document.getElementById('imageModal');
    const modalContent = document.querySelector('.image-modal-content');
    
    if (modal && modalContent) {
        // Limpiar contenido anterior
        modalContent.innerHTML = '';
        
        // Crear embed para PDF
        const pdfEmbed = document.createElement('embed');
        pdfEmbed.src = pdfSrc;
        pdfEmbed.type = 'application/pdf';
        pdfEmbed.style.width = '100%';
        pdfEmbed.style.height = '90vh';
        pdfEmbed.style.border = 'none';
        pdfEmbed.style.borderRadius = '8px';
        
        // Agregar el PDF al modal
        modalContent.appendChild(pdfEmbed);
        
        // Mostrar el modal
        modal.style.display = 'flex';
    }
}

// Función para cerrar modal de imágenes
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    const modalContent = document.querySelector('.image-modal-content');
    
    if (modal) {
        modal.style.display = 'none';
        
        // Restaurar contenido original del modal
        if (modalContent) {
            modalContent.innerHTML = '<img id="modalImage" src="" alt="">';
        }
    }
}

// Cerrar modal con tecla Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeImageModal();
    }
});

// Cerrar modal al hacer click fuera de la imagen
document.addEventListener('click', function(event) {
    const modal = document.getElementById('imageModal');
    const modalContent = document.querySelector('.image-modal-content');
    
    if (modal && event.target === modal) {
        closeImageModal();
    }
});

// Función para animaciones suaves al hacer scroll
function smoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Función para inicializar efectos de hover en tarjetas
function initCardEffects() {
    const cards = document.querySelectorAll('.menu-card, .screenshot-item');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Función para inicializar tooltips (si se necesitan en el futuro)
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                z-index: 1000;
                pointer-events: none;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// Función para manejar el tema (si se implementa en el futuro)
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        body.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
}

// Función para cargar el tema guardado
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }
}

// Función para inicializar todas las funcionalidades
function init() {
    smoothScroll();
    initCardEffects();
    initTooltips();
    loadTheme();
    
    // Agregar clase 'loaded' al body para animaciones CSS
    document.body.classList.add('loaded');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
