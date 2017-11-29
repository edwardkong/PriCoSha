$( document ).ready(function() {
    $("#friendgroup").hide();
});

$("#private").click(function(){
  $('#friendgroup').show();
  $('#friendgroup').attr('required','required');
});

$("#public").click(function(){
  $('#friendgroup').hide();
  $('#friendgroup').removeAttr('required');
});
