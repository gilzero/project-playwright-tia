/**
 * Form validation for the scraper configuration form
 */
function submitForm(event) {
    event.preventDefault();
    
    // Validate form
    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.style.display = 'none';
    errorMessageDiv.innerHTML = '';
    
    // Validate scroll iterations range
    const scrollMinVal = parseInt(document.getElementById('scroll_iterations_min').value);
    const scrollMaxVal = parseInt(document.getElementById('scroll_iterations_max').value);
    if (scrollMinVal > scrollMaxVal) {
        errorMessageDiv.innerHTML = 'Minimum scroll iterations must be less than or equal to maximum.';
        errorMessageDiv.style.display = 'block';
        return false;
    }
    
    // Validate scroll distance range
    const distanceMinVal = parseInt(document.getElementById('scroll_distance_min').value);
    const distanceMaxVal = parseInt(document.getElementById('scroll_distance_max').value);
    if (distanceMinVal > distanceMaxVal) {
        errorMessageDiv.innerHTML = 'Minimum scroll distance must be less than or equal to maximum.';
        errorMessageDiv.style.display = 'block';
        return false;
    }
    
    // Validate sleep range
    const sleepMinVal = parseFloat(document.getElementById('sleep_scroll_min').value);
    const sleepMaxVal = parseFloat(document.getElementById('sleep_scroll_max').value);
    if (sleepMinVal > sleepMaxVal) {
        errorMessageDiv.innerHTML = 'Minimum sleep time must be less than or equal to maximum.';
        errorMessageDiv.style.display = 'block';
        return false;
    }
    
    // Validate URL delay range
    const delayMinVal = parseFloat(document.getElementById('url_delay_min').value);
    const delayMaxVal = parseFloat(document.getElementById('url_delay_max').value);
    if (delayMinVal > delayMaxVal) {
        errorMessageDiv.innerHTML = 'Minimum URL delay must be less than or equal to maximum.';
        errorMessageDiv.style.display = 'block';
        return false;
    }
    
    // Submit the form if validation passes
    document.getElementById('scrapeForm').submit();
    return true;
} 