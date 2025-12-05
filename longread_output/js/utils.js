// Shared utilities and constants

// Color palette with high contrast between consecutive colors
export const colorPalette = {
    vlaanderen: '#e63946', // Red
    provinces: [
        '#2a9d8f', // Teal
        '#d62828', // Red
        '#003049', // Dark blue
        '#f77f00', // Orange
        '#06a77d', // Green
        '#6c5ce7'  // Purple
    ],
    municipalities: [
        '#0055cc', // Blue
        '#ff6b6b', // Coral red
        '#00b894', // Mint green
        '#6c5ce7', // Purple
        '#f9ca24', // Yellow
        '#d63031', // Dark red
        '#4ecdc4', // Turquoise
        '#e17055', // Orange
        '#0984e3', // Bright blue
        '#fd79a8', // Pink
        '#00cec9', // Cyan
        '#fdcb6e', // Peach
        '#2d3436', // Charcoal
        '#55efc4', // Aqua
        '#e84393', // Magenta
        '#74b9ff', // Light blue
        '#a29bfe', // Light purple
        '#ffeaa7', // Light yellow
        '#636e72', // Dark gray
        '#00b894'  // Green
    ],
    domains: [
        '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
        '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5'
    ]
};

// Line and border styles for differentiation
export const lineStyles = [
    { borderDash: [] },           // Solid
    { borderDash: [5, 5] },        // Dashed
    { borderDash: [2, 2] },        // Dotted
    { borderDash: [10, 5, 2, 5] }, // Dash-dot
    { borderDash: [5, 10] },       // Long dash
    { borderDash: [2, 8, 2, 8] }  // Dot-dash
];

// Get color for region based on type and index
export function getColorForRegion(type, index, name) {
    if (type === 'vlaanderen') {
        return colorPalette.vlaanderen;
    } else if (type === 'province') {
        return colorPalette.provinces[index % colorPalette.provinces.length];
    } else if (type === 'municipality') {
        return colorPalette.municipalities[index % colorPalette.municipalities.length];
    }
    return '#0055cc'; // Default
}

// Get line style based on index
export function getLineStyle(index) {
    return lineStyles[index % lineStyles.length];
}

// Intuitive color scale: warm colors (red/orange) = high, cool colors (green/blue) = low
export function getColorScale(d, min, max) {
    const t = (d - min) / (max - min);
    
    if (t >= 0.9) return '#d73027';      // Top 10% - Bright red (high)
    if (t >= 0.7) return '#f46d43';      // 70-90% - Orange-red
    if (t >= 0.5) return '#fdae61';      // 50-70% - Orange-yellow
    if (t >= 0.3) return '#abd9e9';      // 30-50% - Light blue
    if (t >= 0.1) return '#74add1';      // 10-30% - Blue
    return '#4575b4';                    // Bottom 10% - Dark blue (low)
}

// Escape HTML
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format currency
export function formatCurrency(amount) {
    if (amount === 0 || !amount) return '-';
    return '€ ' + amount.toLocaleString('nl-BE', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

// Format currency short (with K/M suffixes)
export function formatCurrencyShort(amount) {
    if (!amount || amount === 0) return '€0';
    if (amount >= 1000000) {
        return '€' + (amount / 1000000).toFixed(0) + 'M';
    } else if (amount >= 1000) {
        return '€' + (amount / 1000).toFixed(0) + 'K';
    }
    return '€' + amount.toFixed(0);
}
