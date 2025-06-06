function Div(el)
  -- Para bloques center
  if el.classes and el.classes[1] == "center" then
    el.attributes["custom-style"] = "Centered"
    return el
  end
  
  -- Para bloques headerblock
  if el.classes and el.classes[1] == "headerblock" then
    el.attributes["custom-style"] = "HeaderLeft"
    return el
  end

  if el.classes and el.classes[1] == "summary" then
    el.attributes["custom-style"] = "Summary"
    return el
  end
  
  return el
end
