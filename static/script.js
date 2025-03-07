function enterClass(classCode) {
    // Logic to load the quiz when the "Take Quiz" button is clicked
    loadQuiz(classCode);

    if (!classCode || typeof classCode !== 'string') {
        console.error('Invalid class code:', classCode);
        alert('Please select a valid class to enter.');
        return;
    }
    
    console.log('Entering class with code:', classCode); // Debugging output
    console.log('Redirecting to:', `/classroom/${classCode}`);
    
    try {
        window.location.href = `/classroom/${classCode}`;
    } catch (error) {
        console.error('Error redirecting to classroom:', error);
        alert('An error occurred while trying to enter the class. Please try again.');
    }
}

function loadQuiz(classCode) {
    fetch(`/classes/${classCode}/quizzes`, {
        method: 'GET'
        // Removed Content-Type header for GET request
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load quizzes');
            }
            return response.json();
        })
        .then(quizzes => {
            console.log('Fetched quizzes:', quizzes); // Debugging: Log fetched quizzes
            // Logic to display quizzes on the page or redirect to the quiz page
            // For example, redirect to the first quiz if available
            if (quizzes.length > 0) {
                window.location.href = `/classes/${classCode}/quizzes/${quizzes[0].id}`;
            } else {
                alert('No quizzes available for this class.');
            }
        })
        .catch(error => {
            console.error('Error loading quizzes:', error);
            alert('An error occurred while loading quizzes. Please try again later.');
        });
}

document.addEventListener('DOMContentLoaded', function() {
    // Fetch and display classes for the teacher dashboard
    if (window.location.pathname === '/teacher_dashboard') {
        fetchClasses();
        fetchStudents();
    }

    // Fetch and display classes for the student dashboard
    if (window.location.pathname === '/student_dashboard') {
        fetchClasses();
    }

    // Function to open the create class modal
    document.getElementById('create-class-button').addEventListener('click', () => {
        const createClassModal = new bootstrap.Modal(document.getElementById('create-class-modal'));
        createClassModal.show();
    });

    // Handle Create Class Form Submission
    document.getElementById('create-class-form').addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent default form submission

        const className = document.getElementById('class-name').value;
        const classDescription = document.getElementById('class-description').value;

        fetch('/create_class', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: className, description: classDescription })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close the modal
                const createClassModal = bootstrap.Modal.getInstance(document.getElementById('create-class-modal'));
                createClassModal.hide();

                // Reload the page to show the new class
                window.location.reload();
            } else {
                alert('Error creating class.');
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Fetch and Display Classes
    function loadClasses() {
        fetch('/api/classes')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch classes');
                }
                return response.json();
            })
            .then(classes => {
                console.log('Fetched classes:', classes.classes); // Debugging: Log fetched classes

                const classList = document.getElementById('class-list');
                classList.innerHTML = ''; // Clear existing classes

                if (classes.length === 0) {
                    classList.innerHTML = '<p>No classes found.</p>'; // Display a message if no classes exist
                } else {
                    classes.forEach(classData => {
                        console.log("Class Data:", classData); // Debugging: Log class data
                        const classElement = document.createElement('div');
                        classElement.className = 'col-md-6 mb-4';
                        classElement.innerHTML = `
                            <div class="card shadow-sm">
                                <div class="card-body">
                                    <h3 class="card-title">${classData.name}</h3>
                                    <p class="card-text">${classData.description}</p>
                                    <button class="btn btn-primary enter-class-button" data-class-code="${classData.id}">Enter Class</button>
                                </div>
                            </div>
                        `;
                        classList.appendChild(classElement);
                    });

                    // Attach event listeners after elements are added
                    document.querySelectorAll('.enter-class-button').forEach(button => {
                        button.addEventListener('click', function() {
                            const classCode = this.getAttribute('data-class-code');
                            enterClass(classCode);
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error loading classes:', error);
                const classList = document.getElementById('class-list');
                classList.innerHTML = '<p>Failed to load classes. Please try again later.</p>'; // Display an error message
            });
    }

    // Fetch and Display Students
    function loadStudents() {
        fetch('/api/students')
            .then(response => response.json())
            .then(students => {
                const studentList = document.getElementById('student-list');
                studentList.innerHTML = ''; // Clear existing students
                students.forEach(student => {
                    const studentElement = document.createElement('div');
                    studentElement.className = 'col-md-6 mb-4';
                    studentElement.innerHTML = `
                        <div class="card shadow-sm">
                            <div class="card-body">
                                <h3 class="card-title">${student.name}</h3>
                                <p class="card-text">${student.email}</p>
                            </div>
                        </div>
                    `;
                    studentList.appendChild(studentElement);
                });
            })
            .catch(error => console.error('Error loading students:', error));
    }

    // Load classes and students on page load
    loadClasses();
    loadStudents();
});
