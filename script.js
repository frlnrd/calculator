const display = document.getElementById('display');

function appendNumber(num) {
    // Remplace le zéro initial par le chiffre saisi (sauf point)
    if (display.value === '0' && num !== '.') {
        display.value = num;
        return;
    }

    // Gestion du point décimal : on empêche un second point dans le même nombre
    if (num === '.') {
        // Recherche du dernier opérateur (+ - * /)
        const lastOperatorIndex = Math.max(
            display.value.lastIndexOf('+'),
            display.value.lastIndexOf('-'),
            display.value.lastIndexOf('*'),
            display.value.lastIndexOf('/')
        );

        // Le nombre en cours commence juste après cet opérateur (ou au début)
        const currentNumber = lastOperatorIndex === -1
            ? display.value
            : display.value.slice(lastOperatorIndex + 1);

        // Si le nombre en cours possède déjà un point → on ignore l’entrée
        if (currentNumber.includes('.')) {
            return;
        }
        // Aucun point présent → on autorise l’ajout du point (sans zéro implicite)
    }

    // Ajout normal du caractère (chiffre ou point valide)
    display.value += num;
}

function appendOperator(operator) {
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