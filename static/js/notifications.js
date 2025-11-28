(() => {
    const STACK_ID = 'notificationStack';
    const DEFAULT_DURATION = 4500;

    const ensureStack = () => {
        let stack = document.getElementById(STACK_ID);
        if (!stack) {
            stack = document.createElement('div');
            stack.id = STACK_ID;
            stack.className = 'notification-stack';
            document.body.appendChild(stack);
        }
        return stack;
    };

    const closeToast = (toast, delay = 0) => {
        setTimeout(() => {
            toast.classList.remove('show');
            toast.addEventListener(
                'transitionend',
                () => toast.remove(),
                { once: true }
            );
        }, delay);
    };

    const buildToast = ({ title, message, type }) => {
        const toast = document.createElement('div');
        toast.className = `notification-toast ${type}`;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-toast__close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => closeToast(toast));

        const titleEl = document.createElement('div');
        titleEl.className = 'notification-toast__title';
        titleEl.textContent = title;

        const messageEl = document.createElement('p');
        messageEl.className = 'notification-toast__message';
        messageEl.textContent = message;

        toast.append(closeBtn, titleEl, messageEl);
        return toast;
    };

    const showNotification = (message, options = {}) => {
        const {
            title = 'Aviso',
            type = 'info',
            duration = DEFAULT_DURATION,
        } = options;

        const stack = ensureStack();
        const toast = buildToast({ title, message, type });
        stack.appendChild(toast);

        requestAnimationFrame(() => toast.classList.add('show'));
        closeToast(toast, duration);
    };

    const createConfirmDialog = (options = {}) => {
        const {
            title = 'Confirmar acción',
            message = '¿Deseás continuar?',
            confirmText = 'Aceptar',
            cancelText = 'Cancelar',
        } = options;

        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'notification-confirm-overlay';

            const dialog = document.createElement('div');
            dialog.className = 'notification-confirm';

            const titleEl = document.createElement('h4');
            titleEl.textContent = title;

            const messageEl = document.createElement('p');
            messageEl.textContent = message;

            const actions = document.createElement('div');
            actions.className = 'notification-confirm__actions';

            const cancelBtn = document.createElement('button');
            cancelBtn.type = 'button';
            cancelBtn.className = 'btn btn-outline-secondary';
            cancelBtn.textContent = cancelText;

            const confirmBtn = document.createElement('button');
            confirmBtn.type = 'button';
            confirmBtn.className = 'btn btn-primary';
            confirmBtn.textContent = confirmText;

            actions.append(cancelBtn, confirmBtn);
            dialog.append(titleEl, messageEl, actions);
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            requestAnimationFrame(() => overlay.classList.add('show'));

            const close = (value) => {
                overlay.classList.remove('show');
                overlay.addEventListener(
                    'transitionend',
                    () => {
                        overlay.remove();
                        resolve(value);
                    },
                    { once: true }
                );
            };

            cancelBtn.addEventListener('click', () => close(false));
            confirmBtn.addEventListener('click', () => close(true));
            overlay.addEventListener('click', (event) => {
                if (event.target === overlay) {
                    close(false);
                }
            });
        });
    };

    const api = {
        show: showNotification,
        success: (msg, opts = {}) => showNotification(msg, { ...opts, type: 'success', title: opts.title || 'Listo' }),
        error: (msg, opts = {}) => showNotification(msg, { ...opts, type: 'error', title: opts.title || 'Error' }),
        warning: (msg, opts = {}) => showNotification(msg, { ...opts, type: 'warning', title: opts.title || 'Atención' }),
        info: (msg, opts = {}) => showNotification(msg, { ...opts, type: 'info', title: opts.title || 'Aviso' }),
        confirm: createConfirmDialog,
    };

    window.notify = api;
})();

