document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('similarName').value;
    const location = document.getElementById('similarLocation').value;
    const industry = document.getElementById('similarIndustry').value;

    const searchLoadingIndicator = document.getElementById('searchLoadingIndicator');
    searchLoadingIndicator.style.display = 'block';

    try {
        const response = await fetch(`/similar_companies/?name=${encodeURIComponent(name)}${location ? `&location=${encodeURIComponent(location)}` : ''}${industry ? `&industry=${encodeURIComponent(industry)}` : ''}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displayCompanySelection(data.similar_companies.companies);
        document.getElementById('similarError').textContent = '';
    } catch (error) {
        document.getElementById('similarError').textContent = error.message;
        document.getElementById('similarResult').innerHTML = '';
    } finally {
        searchLoadingIndicator.style.display = 'none';
    }
});

function displayCompanySelection(companies) {
    const similarDiv = document.getElementById('similarResult');
    similarDiv.innerHTML = '';

    if (!companies || companies.length === 0) {
        similarDiv.innerHTML = '<p class="alert alert-warning">No companies found.</p>';
        return;
    }

    let tableHTML = '<h3 class="mb-3">Select a Company</h3>';
    tableHTML += '<table class="table table-hover table-bordered table-sleek">';
    tableHTML += '<thead class="table-light"><tr><th>Name</th><th>Location</th><th>Industry</th></tr></thead>';
    tableHTML += '<tbody>';

    companies.forEach(company => {
        tableHTML += `<tr class="clickable-row" data-name="${company.name}">
            <td>${company.name}</td>
            <td>${company.location || 'N/A'}</td>
            <td>${company.industry || 'N/A'}</td>
        </tr>`;
    });

    tableHTML += '</tbody></table>';
    similarDiv.innerHTML = tableHTML;

    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', () => {
            const companyName = row.dataset.name;
            getCompanyProfile(companyName);
        });
    });
}

async function getCompanyProfile(name) {
    const profileLoadingIndicator = document.getElementById('profileLoadingIndicator');
    const profileSuccess = document.getElementById('profileSuccess');
    const profileError = document.getElementById('profileError');

    profileLoadingIndicator.style.display = 'block';
    profileSuccess.style.display = 'none';
    profileError.textContent = '';

    try {
        const response = await fetch(`/company_profile/?name=${encodeURIComponent(name)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Company Profile Data:", data); // Debugging
        displayProfile(data);
        profileSuccess.style.display = 'block';
    } catch (error) {
        profileError.textContent = 'Failed to fetch profile: ' + error.message;
        document.getElementById('profileResult').innerHTML = '';
        console.error("Error fetching profile:", error); // Debugging
    } finally {
        profileLoadingIndicator.style.display = 'none';
    }
}

function displayProfile(data) {
    const profileResultDiv = document.getElementById('profileResult');
    profileResultDiv.innerHTML = '';

    if (!data || !data.profile) {
        profileResultDiv.innerHTML = '<p class="alert alert-danger">No profile data available.</p>';
        return;
    }

    const profile = data.profile;

    try {
        let profileHTML = `
            <div class="card">
                <div class="card-body">
                    <h3 class="card-title">${profile.Name || 'N/A'}</h3>
                    <p><strong>Location:</strong> ${profile.Location || 'N/A'}</p>
                    <p><strong>Industry:</strong> ${profile.Industry || 'N/A'}</p>
                    <p><strong>Website:</strong> <a href="${profile.Website || '#'}" target="_blank" class="link-primary">${profile.Website || 'N/A'}</a></p>
                    <p><strong>LinkedIn:</strong> <a href="${profile.LinkedIn || '#'}" target="_blank" class="link-primary">${profile.LinkedIn || 'N/A'}</a></p>
                    <p><strong>Founded Year:</strong> ${profile['Founded Year'] || 'N/A'}</p>
                    <p><strong>Number of Employees:</strong> ${profile['Number of Employees'] || 'N/A'}</p>
                    <p><strong>Revenue:</strong> ${profile['Revenue'] || 'N/A'}</p>
                    <p><strong>Stock Price:</strong> ${profile['Stock Price'] || 'N/A'}</p>
        `;

        if (profile['Top Executives'] && Array.isArray(profile['Top Executives']) && profile['Top Executives'].length > 0) {
            profileHTML += `
                <h4 class="mt-4 mb-3">Top Executives</h4>
                <div class="accordion">
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#executivesCollapse" aria-expanded="true" aria-controls="executivesCollapse">
                                Executives
                            </button>
                        </h2>
                        <div id="executivesCollapse" class="accordion-collapse collapse show">
                            <div class="accordion-body">
                                <table class="table table-striped table-bordered">
                                    <thead class="table-light"><tr><th>Name</th><th>Designation</th><th>LinkedIn</th><th>Email</th></tr></thead>
                                    <tbody>`;
            profile['Top Executives'].forEach(exec => {
                profileHTML += `<tr>
                    <td>${exec.Name}</td>
                    <td>${exec.Position}</td>
                    <td><a href="${exec.LinkedIn}" target="_blank" class="link-info">Link</a></td>
                    <td>${exec.Email || 'N/A'}</td>
                </tr>`;
            });
            profileHTML += `</tbody></table></div></div></div></div>`;
        }

        if (profile['Latest News'] && Array.isArray(profile['Latest News']) && profile['Latest News'].length > 0) {
            console.log("Latest News Array:", profile['Latest News']);
            profileHTML += `
                <h4 class="mt-4 mb-3">Latest News</h4>
                <div class="accordion">
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#newsCollapse" aria-expanded="true" aria-controls="newsCollapse">
                                News
                            </button>
                        </h2>
                        <div id="newsCollapse" class="accordion-collapse collapse show">
                            <div class="accordion-body">`;
            profile['Latest News'].forEach(news => {
                console.log("News Item:", news);

                const title = news.Title || 'Update';
                const date = news.Date || 'N/A';
                const sentiment = news.Sentiment ? `<span class="sentiment">Sentiment: ${news.Sentiment}</span>` : '';
                console.log("News Date:", date);
                console.log("News Sentiment:", sentiment);
                profileHTML += `<div class="card mb-2"><div class="card-body"><h6 class="card-title">${title}</h6><p class="card-text">${news.Summary || 'No summary available.'}</p><p>Date: ${date}</p>${sentiment}</div></div>`;
            });
            profileHTML += `</div></div></div></div>`;
        }

        if (data.sources && Array.isArray(data.sources) && data.sources.length > 0) {
            profileHTML += '<h4 class="mt-4 mb-3">Sources</h4>';
            data.sources.forEach(source => {
                profileHTML += `<p><a href="${source}" target="_blank" class="link-secondary">${source}</a></p>`;
            });
        }

        profileHTML += `</div></div>`;
        console.log("Generated HTML:", profileHTML);
        profileResultDiv.innerHTML = profileHTML;
    } catch (error) {
        console.error("Error displaying profile:", error);
        profileResultDiv.innerHTML = '<p class="alert alert-danger">Error displaying profile.</p>';
    }
}