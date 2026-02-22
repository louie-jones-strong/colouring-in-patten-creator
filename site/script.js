const fileEl = document.getElementById('file');
const spacingEl = document.getElementById('spacing');
const dotSizeEl = document.getElementById('dotSize');
const resizeScaleEl = document.getElementById('resize-scale');
const holderEl = document.getElementById('holder');

let img = new Image();
fileEl.addEventListener('change', e => {
	const f = e.target.files && e.target.files[0];
	if (!f) return;
	const url = URL.createObjectURL(f);
	img = new Image();
	img.onload = () => { URL.revokeObjectURL(url); temp(); };
	img.src = url;
});

[spacingEl, dotSizeEl, resizeScaleEl].forEach(el => el.addEventListener('input', () => { if (img.src) temp(); }));
let resizeScale = 2;
function temp() {
	if (!img.src) {
		return;
	}

	// let resizeScale = parseFloat(resizeScaleEl.value);
	width = img.naturalWidth / resizeScale;
	height = img.naturalHeight / resizeScale;

	// draw image to an offscreen canvas at the requested size and read pixels
	const canvas = document.createElement('canvas');
	canvas.width = width;
	canvas.height = height;
	const ctx = canvas.getContext('2d');
	ctx.imageSmoothingEnabled = false;
	ctx.drawImage(img, 0, 0, width, height);
	const imageData = ctx.getImageData(0, 0, width, height).data;

	html = '';
	for (let y = 0; y < height; y++) {
		html += `<div class="row">`;
		for (let x = 0; x < width; x++) {
			const idx = (y * width + x) * 4;
			const r = imageData[idx];
			const g = imageData[idx + 1];
			const b = imageData[idx + 2];
			const intensity = 0.2126 * r + 0.7152 * g + 0.0722 * b;

			let scale = 1 - intensity / 255;
			html += `<div class="item" style="--scale: ${scale}"></div>`;
		}
		html += `</div>`;
	}
	holderEl.innerHTML = html;

}
// Mark an item as filled when clicked(only set, do not toggle off)
holderEl.addEventListener('click', (e) => {
	const item = e.target.closest('.item');
	if (!item) return;
	if (!item.classList.contains('filled')) {
		item.classList.add('filled');
	}
});
