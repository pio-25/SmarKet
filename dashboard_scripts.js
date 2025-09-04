document.addEventListener('DOMContentLoaded', () => {
    // Check user role for authentication
    const userRole = localStorage.getItem('userRole');
    const path = window.location.pathname;

    if (path.includes('seller_dashboard.html') && userRole !== 'seller') {
        alert('Access Denied. Please log in as a Seller.');
        window.location.href = 'index.html#form';
        return;
    }

    if (path.includes('admin_dashboard.html') && userRole !== 'admin') {
        alert('Access Denied. Please log in as an Admin.');
        window.location.href = 'index.html#form';
        return;
    }



    const productUploadForm = document.getElementById('product-upload-form');
    const productList = document.getElementById('product-list');
    const allProductList = document.getElementById('all-product-list');

    // Fetch products from the API instead of localStorage
    const fetchProducts = async () => {
        try {
            const response = await fetch('/api/products');
            const products = await response.json();
            if (productList) {
                renderProducts(productList, products);
            }
            if (allProductList) {
                renderProducts(allProductList, products);
            }
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    };

    // Fetch sellers from the API instead of localStorage
    const fetchSellers = async () => {
        try {
            const response = await fetch('/api/admin/sellers');
            const sellers = await response.json();
            renderSellers(sellers);
        } catch (error) {
            console.error('Error fetching sellers:', error);
        }
    };

    // // Mock data storage for demonstration purposes
    // let products = JSON.parse(localStorage.getItem('products')) || [];
    // let sellers = JSON.parse(localStorage.getItem('sellers')) || [
    //     { id: 'seller-1', name: 'Pia', status: 'Active' },
    //     { id: 'seller-2', name: 'Sandesh', status: 'Pending' }
    // ];

    // Render sellers table for admin dashboard
    function renderSellers() {
        const sellerTableBody = document.querySelector('#seller-table tbody');
        if (sellerTableBody) {
            sellerTableBody.innerHTML = '';
            sellers.forEach(seller => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${seller.id}</td>
                    <td>${seller.name}</td>
                    <td>${seller.status}</td>
                    <td>
                        <button class="action-btn approve">Approve</button>
                        <button class="action-btn reject">Reject</button>
                    </td>
                `;
                sellerTableBody.appendChild(row);
            });
        }
    }

    // Render products for both seller and admin dashboards
    function renderProducts(container, data) {
        if (container) {
            container.innerHTML = '';
            data.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.innerHTML = `
                    <img src="${product.image}" alt="${product.name}">
                    <div class="product-info">
                        <h4>${product.name}</h4>
                        <p class="price">Rs.${product.price.toFixed(2)}</p>
                        <p>${product.description}</p>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    }

    // Handle product upload form submission
    // Handle product upload form submission
    if (productUploadForm) {
        productUploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const name = document.getElementById('product-name').value;
            const price = parseFloat(document.getElementById('product-price').value);
            const description = document.getElementById('product-description').value;
            const imageFile = document.getElementById('product-image').files[0];

            if (imageFile) {
                const reader = new FileReader();
                reader.onload = async (event) => {
                    const newProduct = {
                        name,
                        price,
                        description,
                        image: event.target.result // Base64 image
                    };

                    try {
                        const response = await fetch('/api/products', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(newProduct)
                        });
                        if (response.ok) {
                            alert('Product uploaded successfully!');
                            productUploadForm.reset();
                            fetchProducts(); // Re-fetch and re-render the products
                        } else {
                            alert('Failed to upload product.');
                        }
                    } catch (error) {
                        console.error('Error uploading product:', error);
                        alert('An error occurred. Please try again.');
                    }
                };
                reader.readAsDataURL(imageFile);
            }
        });
    }
    // if (productUploadForm) {
    //     productUploadForm.addEventListener('submit', (e) => {
    //         e.preventDefault();

    //         const name = document.getElementById('product-name').value;
    //         const price = parseFloat(document.getElementById('product-price').value);
    //         const description = document.getElementById('product-description').value;
    //         const imageFile = document.getElementById('product-image').files[0];

    //         if (imageFile) {
    //             const reader = new FileReader();
    //             reader.onload = (event) => {
    //                 const newProduct = {
    //                     id: `prod-${Date.now()}`,
    //                     name,
    //                     price,
    //                     description,
    //                     image: event.target.result
    //                 };

    //                 products.push(newProduct);
    //                 localStorage.setItem('products', JSON.stringify(products));

    //                 renderProducts(productList, products);
    //                 productUploadForm.reset();
    //                 alert('Product uploaded successfully!');
    //             };
    //             reader.readAsDataURL(imageFile);
    //         }
    //     });


    // Initial render for seller's dashboard
    if (productList) {
        fetchProducts();
    }

    // Initial render for admin's dashboard
    if (allProductList) {
        fetchProducts();
    }

    // Initial render for admin's dashboard seller table
    if (document.getElementById('seller-table')) {
        fetchSellers();
    }

});