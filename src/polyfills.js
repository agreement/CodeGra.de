import { TextDecoder } from 'text-encoding';
import URLSearchParams from 'url-search-params';

Element.prototype.matches = Element.prototype.matches || Element.prototype.msMatchesSelector;
Math.log10 = Math.log10 || (x => Math.log(x) / Math.LN10);

window.TextDecoder = window.TextDecoder || TextDecoder;
window.URLSearchParams = window.URLSearchParams || URLSearchParams;

// eslint-disable-next-line
Array.prototype.findIndex = Array.prototype.findIndex || function findIndex(callback) {
    if (this === null) {
        throw new TypeError('Array.prototype.findIndex called on null or undefined');
    } else if (typeof callback !== 'function') {
        throw new TypeError('callback must be a function');
    }

    const list = Object(this);
    // Makes sures is always has an positive integer as length.
    // eslint-disable-next-line
    const length = list.length >>> 0;
    // eslint-disable-next-line
    const thisArg = arguments[1];

    for (let i = 0; i < length; i++) {
        if (callback.call(thisArg, list[i], i, list)) {
            return i;
        }
    }
    return -1;
};

Element.prototype.closest = Element.prototype.closest || function closest(s) {
    let el = this;

    if (!document.documentElement.contains(el)) {
        return null;
    }

    for (;
        el !== null && el.nodeType === Node.ELEMENT_NODE;
        el = el.parentElement || el.parentNode
    ) {
        if (el.matches(s)) {
            return el;
        }
    }
    return null;
};
