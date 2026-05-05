document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("add-form-row");
    const container = document.getElementById("medicine-formset");
    const template = document.getElementById("empty-form-template");
    const totalForms = document.querySelector('input[name$="-TOTAL_FORMS"]');

    if (!addButton || !container || !template || !totalForms) {
        return;
    }

    addButton.addEventListener("click", () => {
        const index = Number(totalForms.value);
        const html = template.innerHTML.replaceAll("__prefix__", index);
        container.insertAdjacentHTML("beforeend", html);
        totalForms.value = index + 1;
    });
});
