// Search functionality for student table
document.getElementById('searchMarks').addEventListener('input', function() {
    let filter = this.value.toLowerCase();
    let rows = document.querySelectorAll('#marksTable tbody tr');
    rows.forEach(row => {
        let text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
});

// Handle delete modal population
const deleteModal = document.getElementById('deleteModal');
if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget; // Button that triggered the modal
        const studentId = button.getAttribute('data-student-id');
        const studentName = button.getAttribute('data-student-name');
        
        // Update modal content
        const modalStudentName = deleteModal.querySelector('#studentName');
        const modalStudentId = deleteModal.querySelector('#studentId');
        
        modalStudentName.textContent = studentName;
        modalStudentId.value = studentId;
    });
}

// Client-side validation for registration form
function validateRegisterForm() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return false;
    }
    
    if (password.length < 8) {
        alert('Password must be at least 8 characters long!');
        return false;
    }
    
    return true;
}