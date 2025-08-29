/* eslint-disable react/jsx-key */
import React from 'react'

const Container = () => <main className="container">{{children}}</main>

export default function App() {
  return (
    <Container><h1 className="text">login</h1><p className="text">Email</p><label className="label"></label>
          <input className="input" type="text" placeholder="email" /><p className="text">Password</p><label className="label"></label>
          <input className="input" type="password" placeholder="password" /><button className={"btn " + ("primary" if el.style.variant == 'primary' else "secondary")}>Continue</button><img className="image" src="" alt="image_img_box" /><p className="text">© Piyush 2025</p>    </Container>
  )
}