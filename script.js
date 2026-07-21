const display = document.getElementById('display');

// -------------------------------------------------
// Helper : remet le display à zéro si son contenu
// n’est plus une valeur numérique exploitable.
// -------------------------------------------------
function resetIfInvalid() {
    const num = Number(display.value);
    // Number('NaN') => NaN, Number('Error') => NaN, Infinity => Infinity
    if (!Number.isFinite(num) || Number.isNaN(num)) {
        // Utilise clearDisplay() pour garder le même style/effet visuel
        clearDisplay();
    }
}

function appendNumber(num) {
    // Si le display montre une erreur, on le réinitialise
    resetIfInvalid();

    if (display.value === '0' && num !== '.') {
        display.value = num;
    } else if (num === '.' && display.value.includes('.')) {
        return;
    } else {
        display.value += num;
    }
}

function appendOperator(operator) {
    // Même logique que pour les chiffres : on repart d’un état « propre »
    resetIfInvalid();

    const lastChar = display.value[display.value.length - 1];
    
    // Prevent multiple operators in a row
    if (['+', '-', '*', '/'].includes(lastChar)) {
        return;
    }
    
    // Prevent operator as first input
    if (display.value === '') {
        return;
    }
    
    display.value += operator;
}

function clearDisplay() {
    display.value = '0';
}

function deleteLast() {
    if (display.value.length > 1) {
        display.value = display.value.slice(0, -1);
    } else {
        display.value = '0';
    }
}

function calculate() {
    try {
        const lastChar = display.value[display.value.length - 1];
        
        // Prevent calculation if expression ends with operator
        if (['+', '-', '*', '/'].includes(lastChar)) {
            return;
        }
        
        const result = Function('"use strict"; return (' + display.value + ')')();
        
        // Replace Infinity / -Infinity with NaN
        if (!isFinite(result)) {
            display.value = 'NaN';
        } else {
            display.value = result;
        }
    } catch (error) {
        display.value = 'Error';
        setTimeout(() => {
            display.value = '0';
        }, 1500);
    }
}

// Initialize display
display.value = '0';

// Keyboard support
document.addEventListener('keydown', (e) => {
    if (e.key >= '0' && e.key <= '9') {
        appendNumber(e.key);
    } else if (e.key === '.') {
        appendNumber('.');
    } else if (e.key === '+' || e.key === '-' || e.key === '*' || e.key === '/') {
        appendOperator(e.key);
    } else if (e.key === 'Enter' || e.key === '=') {
        e.preventDefault();
        calculate();
    } else if (e.key === 'Backspace') {
        deleteLast();
    } else if (e.key === 'Escape') {
        clearDisplay();
    }
});