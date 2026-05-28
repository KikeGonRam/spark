document.addEventListener('alpine:init', () => {
  Alpine.data('barberproModal', ({ id='modal', size='md' } = {}) => ({
    id,
    open: false,
    title: '',
    subtitle: '',
    showClose: true,
    size,
    panelClasses: '',
    init() {
      const sizeMap = {
        'sm': 'max-w-md',
        'md': 'max-w-2xl',
        'lg': 'max-w-4xl',
        'xl': 'max-w-6xl',
        'full': 'max-w-none w-full h-full sm:h-auto'
      }
      this.panelClasses = `${sizeMap[this.size] || sizeMap.md} w-full`;
      // body lock
      this.$watch('open', value => {
        if (value) document.documentElement.classList.add('overflow-hidden');
        else document.documentElement.classList.remove('overflow-hidden');
      });
      // focus
      this.$watch('open', async (v) => {
        if (v) {
          await this.$nextTick();
          const focusable = this.$el.querySelector('input,select,textarea,button,a,[tabindex]:not([tabindex="-1"])');
          if (focusable) focusable.focus();
        }
      });

      // global open/close events
      window.addEventListener('open-modal', e => { if (!e.detail || e.detail.id === this.id) this.openModal(e.detail || {}); });
      window.addEventListener('close-modal', e => { if (!e.detail || e.detail.id === this.id) this.close(); });
    },
    openModal(payload = {}) {
      if (payload.title) this.title = payload.title;
      if (payload.subtitle) this.subtitle = payload.subtitle;
      this.open = true;
    },
    close() { this.open = false; },
    clickOutside(e) { if (e.target === e.currentTarget) this.close(); }
  }));
});
