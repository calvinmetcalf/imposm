function (doc){
if(doc.geometry){
emit(doc.geometry, doc);
}
}
