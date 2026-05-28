/**
 * BarberPro Elite - Main JavaScript Entry Point
 * 
 * Imports Alpine.js for interactivity and initializes the frontend.
 */

import Alpine from 'alpinejs';
import '../css/styles.css';

// ==========================================
// Alpine.js Initialization
// ==========================================

// Debuglog para desarrollo
window.Alpine = Alpine;

// Inicializar Alpine.js
document.addEventListener('DOMContentLoaded', () => {
  Alpine.start();
  console.log('✓ Alpine.js initialized');
});

// ==========================================
// Global Utilities
// ==========================================

/**
 * API Client - Wrapper para fetch requests
 */
class APIClient {
  constructor(baseURL = '/api') {
    this.baseURL = baseURL;
    this.token = this.getToken();
  }

  /**
   * Obtener token JWT del localStorage
   */
  getToken() {
    return localStorage.getItem('access_token');
  }

  /**
   * Guardar token JWT
   */
  setToken(token) {
    localStorage.setItem('access_token', token);
    this.token = token;
  }

  /**
   * Headers para solicitud
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  /**
   * GET request
   */
  async get(endpoint) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return response.json();
  }

  /**
   * POST request
   */
  async post(endpoint, data) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  }

  /**
   * PATCH request
   */
  async patch(endpoint, data) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return response.json();
  }
}

// Global API client
window.api = new APIClient();

// ==========================================
// Notification System
// ==========================================

/**
 * Toast notifications
 */
class Notification {
  static show(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notification-container') || 
                     this.createContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} animate-slide-up`;
    toast.innerHTML = `
      <div class="flex items-center justify-between">
        <span>${message}</span>
        <button onclick="this.parentElement.parentElement.remove()" class="text-lg font-bold">&times;</button>
      </div>
    `;

    container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => toast.remove(), duration);
    }

    return toast;
  }

  static success(message, duration = 3000) {
    return this.show(message, 'success', duration);
  }

  static error(message, duration = 5000) {
    return this.show(message, 'danger', duration);
  }

  static warning(message, duration = 4000) {
    return this.show(message, 'warning', duration);
  }

  static info(message, duration = 3000) {
    return this.show(message, 'info', duration);
  }

  static createContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-md';
    document.body.appendChild(container);
    return container;
  }
}

window.Notification = Notification;

// ==========================================
// Authentication State
// ==========================================

/**
 * Auth manager
 */
class AuthManager {
  constructor() {
    this.user = this.loadUser();
    this.isAuthenticated = !!this.user;
  }

  /**
   * Cargar usuario desde localStorage
   */
  loadUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  /**
   * Guardar usuario
   */
  saveUser(user) {
    this.user = user;
    this.isAuthenticated = !!user;
    localStorage.setItem('user', JSON.stringify(user));
    window.dispatchEvent(new Event('auth-changed'));
  }

  /**
   * Hacer logout
   */
  logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.user = null;
    this.isAuthenticated = false;
    window.dispatchEvent(new Event('auth-changed'));
  }

  /**
   * Verificar si usuario tiene rol
   */
  hasRole(role) {
    return this.user?.role === role;
  }

  /**
   * Verificar si usuario tiene permiso
   */
  hasPermission(permission) {
    return this.user?.permissions?.includes(permission) || 
           this.hasRole('admin');
  }
}

window.auth = new AuthManager();

// ==========================================
// Form Helper
// ==========================================

/**
 * Validación y submit de formularios
 */
class FormHelper {
  static async submit(form, endpoint, method = 'POST') {
    try {
      // Validar formulario HTML5
      if (!form.checkValidity()) {
        form.reportValidity();
        return false;
      }

      // Extraer datos del formulario
      const formData = new FormData(form);
      const data = Object.fromEntries(formData);

      // Enviar solicitud
      const response = await window.api[method.toLowerCase()](endpoint, data);

      if (response.success) {
        Notification.success('Operación exitosa');
        form.reset();
        return response.data;
      } else {
        Notification.error(response.message || 'Error en la solicitud');
        return null;
      }
    } catch (error) {
      Notification.error('Error al procesar solicitud: ' + error.message);
      console.error(error);
      return null;
    }
  }

  /**
   * Validar email
   */
  static validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }

  /**
   * Validar contraseña
   */
  static validatePassword(password) {
    const hasMinLength = password.length >= 8;
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*()-_=+[\]{}|;:'",.<>?/`~]/.test(password);

    return {
      valid: hasMinLength && hasUppercase && hasLowercase && hasNumber && hasSpecial,
      minLength: hasMinLength,
      uppercase: hasUppercase,
      lowercase: hasLowercase,
      number: hasNumber,
      special: hasSpecial,
    };
  }
}

window.FormHelper = FormHelper;

// ==========================================
// Page Loading
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  console.log('✓ BarberPro Elite frontend loaded');
  console.log('✓ API client ready');
  console.log('✓ Auth manager ready');
});

// ==========================================
// Export for modules
// ==========================================

export { APIClient, Notification, AuthManager, FormHelper };
