
async function getUserData(){
    const response = await fetch('/api/users');
    return response.json();
}

function loadTable(users){
    const table = document.querySelector('#result');
    if (!table) {
        // Element doesn't exist on this page, skip execution
        return;
    }
    for(let user of users){
        table.innerHTML += `<tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
        </tr>`;
    }
}

async function main(){
    // Only run if we're on a page that needs this functionality
    const table = document.querySelector('#result');
    if (!table) {
        return;
    }
    const users = await getUserData();
    loadTable(users);
}

main();