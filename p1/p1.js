"use strict";

const ingredients = ["3/4 c. butter, softened", "3/4 c. white sugar", "3/4 c. packed light brown sugar", "2 eggs", "1 tsp. vanilla extract", "1 1/4 c. all-purpose flour", "1 tsp. baking soda", "3/4 tsp. ground cinnamon", "1/2 tsp. salt", "2 3/4 c. rolled oats", "1 c. raisins"];

const get_random_color = () => {
  let letters = '0123456789ABCDEF';
  let color = '#';
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

let $title_h1;
let $apply_button;
let $colorbox_div;
let $recipetext_p;
let $recipelist_ul;
let $graffiti_p;


const apply_changes = () => {
  change_title();
  change_recipe_text();
  change_recipe_list();
  change_graffiti();
}

const change_title = () => {
  $title_h1.text("HW9 P1 DONE :)");
}

const change_color = () => {
  $colorbox_div.css("background-color", get_random_color());
}

const change_recipe_text = () => {
  $recipetext_p.css("font-size", "24px");
}

const change_recipe_list = () => {
  for (let i = 0; i < ingredients.length; i++) {
    $recipelist_ul.append(`<li>${ingredients[i]}</li>`);
  }
}

const change_graffiti = () => {
  $graffiti_p.text("PENGUINZ RULE");
}



$(document).ready(() => {
  $title_h1 = $(".title");
  $apply_button = $("#changebutton");
  $colorbox_div = $(".colorbox");
  $recipetext_p = $(".recipetext");
  $recipelist_ul = $(".recipelist");
  $graffiti_p = $(".graffiti");
  $apply_button.click(apply_changes);
  $colorbox_div.click(change_color);
});

