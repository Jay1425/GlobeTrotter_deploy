/**
 * UI Effects Manager
 * Handles animations, transitions, and UI effects
 */

class UIEffects {
    constructor() {
        this.observer = null;
        this.initialize();
    }

    initialize() {
        this.setupIntersectionObserver();
        this.observeAnimatedElements();
        this.setupButtonEffects();
    }

    setupIntersectionObserver() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.animationPlayState = 'running';
                        entry.target.style.opacity = '1';
                    }, index * 100);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
    }

    observeAnimatedElements() {
        document.querySelectorAll('.animate-fadeInUp, .animate-slideInLeft, .animate-slideInRight, .animate-slideInScale')
            .forEach((el, index) => {
                el.style.animationPlayState = 'paused';
                el.style.opacity = '0';
                this.observer.observe(el);
            });
    }

    setupButtonEffects() {
        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {
            button.addEventListener('click', this.createRippleEffect.bind(this));
        });
    }

    createRippleEffect(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            pointer-events: none;
            animation: ripple 0.6s linear;
        `;

        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white transform translate-x-full transition-transform duration-300 ${
            type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(full)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    window.uiEffects = new UIEffects();
    
    // Make showNotification globally available
    window.showNotification = UIEffects.showNotification;
});
