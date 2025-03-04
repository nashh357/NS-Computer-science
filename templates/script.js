document.addEventListener('DOMContentLoaded', function() {
    const classList = document.getElementById('class-list');
    const createClassForm = document.getElementById('create-class-form');

    // Function to load classes from Firestore
    function loadClasses() {
        fetch('/classes')
            .then(response => response.json())
            .then(classes => {
                classList.innerHTML = ''; // Clear existing classes
                for (const classId in classes) {
                    const classData = classes[classId];
                    const classElement = document.createElement('div');
                    classElement.innerHTML = `<h3>${classData.name}</h3><p>Code: ${classData.code}</p>`;
                    classList.appendChild(classElement);
                }
            })
            .catch(error => console.error('Error loading classes:', error));
    }

    // Event listener for creating a new class
    createClassForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const className = document.getElementById('class-name').value;
        const createdBy = 'teacher123'; // Replace with actual user ID

        fetch('/classes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: className, createdBy: createdBy })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Class created:', data);
            loadClasses(); // Reload classes after creation
        })
        .catch(error => console.error('Error creating class:', error));
    });

    loadClasses(); // Initial load of classes
});
