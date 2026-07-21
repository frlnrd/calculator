// script.js

const display = document.getElementById('display');

// -------------------------------------------------
// Helper : remet le display à zéro si son contenu
// n’est plus une valeur numérique exploitable.
// -------------------------------------------------
function resetIfInvalid() {
    const num = Number(display.value);
    // Number('NaN') => NaN, Number('Error') => NaN, Infinity => Infinity
    if (!Number.isFinite(num) || Number.isNaN(num)) {
        clearDisplay(); // utilise la même logique que le bouton C
    }
}

function clearDisplay() {
    display.value = '0';
}

function appendNumber(num) {
    // Si le display montre une erreur, on le réinitialise
    resetIfInvalid();

    if (display.value === '0' && num !== '.') {
        display.value = num;
    } else if (num === '.' && display.value.includes('.')) {
        return; // évite plusieurs points décimaux
    } else {
        display.value += num;
    }
}

function appendOperator(operator) {
    // Même logique que pour les chiffres : on repart d’un état « propre »
    resetIfInvalid();

    const lastChar = display.value[display.value.length - 1];
    // Empêche d'avoir plusieurs opérateurs consécutifs
    if (['+', '-', '*', '/'].includes(lastChar)) {
        return;
    }
    display.value += operator;
}

function calculate() {
    try {
        const lastChar = display.value[display.value.length - 1];
        // Si le dernier caractère est un opérateur, on le retire avant le calcul
        if (['+', '-', '*', '/'].includes(lastChar)) {
            display.value = display.value.slice(0, -1);
        }
        // Évaluation sécurisée de l'expression
        const result = Function('"use strict"; return (' + display.value + ')')();
        // Si le résultat n'est pas fini (Infinity, -Infinity, NaN) → affichage NaN
        if (!Number.isFinite(result) || Number.isNaN(result)) {
            display.value = 'NaN';
        } else {
            display.value = result;
        }
    } catch (e) {
        // En cas d'erreur de syntaxe ou autre, on indique Error
        display.value = 'Error';
    }
}

// -------------------------------------------------
// Gestion des événements (exemple simple)
// -------------------------------------------------
document.querySelectorAll('.num').forEach(btn => {
    btn.addEventListener('click', () => appendNumber(btn.dataset.value));
});

document.querySelectorAll('.op').forEach(btn => {
    btn.addEventListener('click', () => appendOperator(btn.dataset.value));
});

document.getElementById('equals').addEventListener('click', calculate);

document.getElementById('clear').addEventListener('click', clearDisplay);
