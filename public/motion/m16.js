const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const errorMessage = document.getElementById('errorMessage');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
}
);
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFiles(e.dataTransfer.files[0]);
    }
}
);
fileInput.addEventListener('change', () => {
    if (fileInput.files.length)
        handleFiles(fileInput.files[0]);
}
);

async function handleFiles(file) {
    if (!file)
        return;

    errorMessage.style.display = 'none';
    errorMessage.textContent = '';

    const userHash = crypto.randomUUID();
    const formData = new FormData();
    formData.append('main_looks[]', file);
    formData.append('user_hash', userHash);

    try {
        dropZone.querySelector('p').textContent = 'Uploading...';
        const response = await fetch('https://api.fourmula.ai/v1/upload', {
            method: 'POST',
            body: formData
        });
        if (!response.ok)
            throw new Error(`Upload failed with status: ${response.status}`);

        const result = await response.json();
        const data = result.data;
        const projectId = data.project_id;

        let pdpId = null;
        if (data.mainLook) {
            pdpId = data.mainLook.pdp_id;
        }

        if (projectId && pdpId) {
            const redirectUrl = `https://app.fourmula.ai/project/create-pdp/preview/?pdpId=${pdpId}&projectId=${projectId}&userHash=${userHash}`;
            window.location.href = redirectUrl;
        } else {
            throw new Error('Missing project_id or pdp_id in response');
        }

    } catch (error) {
        console.error('Error:', error);
    }
}