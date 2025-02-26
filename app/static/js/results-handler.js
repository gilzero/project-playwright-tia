/**
 * Results page functionality for displaying article details and exporting data
 */

// Global variable to store articles data
let articlesData = [];

/**
 * Initialize the results page with the articles data
 * @param {Array} articles - The articles data
 */
function initResultsPage(articles) {
    articlesData = articles;
    console.log(`Initialized results page with ${articlesData.length} articles`);
}

/**
 * Show article details in a modal
 * @param {string} articleId - The ID of the article to show
 */
function showDetails(articleId) {
    const article = articlesData.find(a => a.article_id === articleId);
    
    if (article) {
        const modalBody = document.getElementById('articleModalBody');
        let content = `
            <div class="card mb-3">
                <div class="card-header">
                    <h5>${article.title}</h5>
                </div>
                <div class="card-body">
                    <p><strong>Article ID:</strong> ${article.article_id}</p>
                    <p><strong>Source:</strong> ${article.source || 'N/A'}</p>
                    <p><strong>Posted Time:</strong> ${article.posted_time || article.relative_time}</p>
                    <p><strong>Categories:</strong> ${article.categories.join(', ') || 'None'}</p>
                    <p><strong>Tags:</strong> ${article.tags.join(', ') || 'None'}</p>
                    <p><strong>URL:</strong> <a href="${article.article_url}" target="_blank">${article.article_url}</a></p>
                    ${article.image_url ? `<p><strong>Image:</strong> <img src="${article.image_url}" class="img-fluid" alt="Article image"></p>` : ''}
                    ${article.content ? `<hr><h6>Content:</h6><p>${article.content}</p>` : ''}
                </div>
            </div>
        `;
        
        modalBody.innerHTML = content;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('articleModal'));
        modal.show();
    } else {
        console.error(`Article with ID ${articleId} not found`);
    }
}

/**
 * Export articles data to CSV
 */
function exportToCSV() {
    if (!articlesData || articlesData.length === 0) {
        console.error('No articles data available for export');
        return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Get all possible headers
    const headers = Object.keys(articlesData[0]).filter(key => key !== 'content');
    csvContent += headers.join(",") + "\r\n";
    
    // Add data rows
    articlesData.forEach(article => {
        let row = headers.map(header => {
            let value = article[header];
            // Handle arrays
            if (Array.isArray(value)) {
                value = `"${value.join('; ')}"`;
            } 
            // Handle strings with commas
            else if (typeof value === 'string' && value.includes(',')) {
                value = `"${value}"`;
            }
            // Handle undefined or null
            else if (value === undefined || value === null) {
                value = '';
            }
            return value;
        });
        csvContent += row.join(",") + "\r\n";
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `techinasia_articles_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`Exported ${articlesData.length} articles to CSV`);
} 