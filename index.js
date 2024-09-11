
async function deleteMember(id){
    console.log(id);
    if (confirm(`Are you sure you want to remove ${id} ?`)) {
        
        console.log('confirmed');
        let promise= await fetch('/api/member/'+id);
        if (promise.status==200){
            let response= await promise.json();
            console.log(response)
            if(response['successfull']==true){
                location.reload()
            }
            else if( response['teamlead']==true){
                alert("You can not remove a team lead");
            }
            else {
                alert("Something went wrong. Try again!")
            }
        }
        else{
            alert("Invalid Dc ID")
        }
    
    } 
    else {
        console.log('Cancelled');
    }
}