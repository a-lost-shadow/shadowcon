$.fn.makeChildrenSameHeight = function() {

    $(this).each(function(){
        var tallest = 0;

        $(this).children().each(function(i){
            if (tallest < $(this).height()) { tallest = $(this).height(); }
        });
        $(this).children().css({'height': tallest});
    });

    return this;
};
