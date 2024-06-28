async def save_img(BASE_URL, headers, session, photo_list, article, folder):
    img = 1
    for photo in photo_list:
        content = await session.get(BASE_URL + photo, headers=headers)
        img_data = await content.read()

        with open(f'./result/{folder}/{article}_{img}.png', "wb") as f:
            f.write(img_data)
            img += 1

