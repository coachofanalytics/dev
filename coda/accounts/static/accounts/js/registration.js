// Updated category and subcategory data based on choices.py
const categorySubcategories = {
    1: { // APPLICANT
        name: "Applicant Subcategories", 
        options: [
            {value: 1, text: "Full Time - Full-time positions"},
            {value: 2, text: "Contract - Contract work"},
            {value: 3, text: "Internship - Internship opportunities"},
        ]
    },
    2: { // STUDENT
        name: "Student Subcategories",
        options: [
            {value: 1, text: "Data Analytics - Data Science, Data Analysis courses"},
            {value: 2, text: "Programming - Programming, Software Development courses"},
            {value: 3, text: "Other - Business/Technical/Other courses"}
        ]
    },
    3: { // CONSULTANT
        name: "Consultant Subcategories",
        options: [
            {value: 1, text: "Technical - Technical consulting, system architecture"},
            {value: 2, text: "Business - Business strategy, operations consulting"},
            {value: 3, text: "Career - Career development, job placement"},
            {value: 4, text: "Project - Project management, implementation"}
        ]
    },
    4: { // INVESTOR
        name: "Investor Subcategories",
        options: [
            {value: 1, text: "Angel - Angel investors, early-stage"},
            {value: 2, text: "VC - Venture capital, growth-stage"},
            {value: 3, text: "Private - Private equity, mature companies"},
            {value: 4, text: "Individual - Personal investors, KCC/loans"}
        ]
    },
    5: { // EXPLORER
        name: "Explorer Subcategories",
        options: [
            {value: 1, text: "Research - Information seekers, prospects"},
            {value: 2, text: "Networking - Industry professionals, networking"},
            {value: 3, text: "Learning - Exploring learning paths"},
            {value: 4, text: "Partnership - Exploring partnerships/business"}
        ]
    }
};

function toggle_sub_selection(categoryValue) {
    const subSelection = document.getElementById('sub_selection');
    const subCategorySelect = document.getElementById('id_sub_category');
    
    if (categoryValue && categoryValue !== '') {
        // Clear existing options
        subCategorySelect.innerHTML = '<option value="" selected>Select Sub Category</option>';
        
        // Get subcategories for selected category
        const categoryData = categorySubcategories[parseInt(categoryValue)];
        if (categoryData) {
            // Add subcategory options
            categoryData.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = option.text;
                subCategorySelect.appendChild(optionElement);
            });
            
            subSelection.style.display = 'block';
        }
    } else {
        subSelection.style.display = 'none';
    }
}

function checkSubCategoryValidity() {
    const categorySelect = document.getElementById('id_category');
    const subCategorySelect = document.getElementById('id_sub_category');
    
    if (categorySelect.value && subCategorySelect.value) {
        // Both are selected, form is valid
        return true;
    }
    
    return false;
}

// Phone number formatting function
function formatPhoneNumber(phoneNumber) {
    // Remove all non-digit characters
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // Check if it's a US number (10 digits) or international (11+ digits)
    if (cleaned.length === 10) {
        // Format as US number: (123) 456-7890
        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
        // Format as US number with country code: +1 (234) 567-8900
        return `+1 (${cleaned.slice(1,4)}) ${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
    } else if (cleaned.length > 10) {
        // International number: +[country code] [number]
        return `+${cleaned}`;
    }
    
    return phoneNumber; // Return as-is if can't format
}

// Add phone input event listener
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('id_phone');
    if (phoneInput) {
        phoneInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = formatPhoneNumber(this.value);
            }
        });
        
        // Allow user to type freely, format on blur
        phoneInput.addEventListener('input', function() {
            // Remove formatting for easier typing
            this.value = this.value.replace(/[^\d+\-\(\)\s]/g, '');
        });
    }
});